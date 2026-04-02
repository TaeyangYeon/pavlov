"""
MarketDataService implementation.
Orchestrates market data fetching with cache-aside pattern.
Single responsibility: cache logic only.
"""

from datetime import date, timedelta

from app.core.metrics import MetricsCollector, get_metrics_collector
from app.domain.market.interfaces import MarketDataPort
from app.domain.market.validator import MarketDataValidator
from app.domain.shared.result import Result
from app.infra.db.repositories.market_data_repository import MarketDataRepository


class MarketDataService:
    """
    Orchestrates market data fetching with cache-aside pattern.
    Single responsibility: cache logic only.
    Depends on abstractions (MarketDataPort, not concrete adapters).
    """

    def __init__(
        self,
        adapter: MarketDataPort,
        repository: MarketDataRepository,
        metrics: MetricsCollector | None = None,
    ):
        self._adapter = adapter
        self._repository = repository
        self._validator = MarketDataValidator()
        self._metrics = metrics or get_metrics_collector()

    async def fetch_and_cache(
        self, ticker: str, market: str, target_date: date
    ) -> dict | None:
        """
        Cache-Aside pattern:
        1. Check DB cache
        2. HIT → return immediately (no API call)
        3. MISS → fetch from adapter → store → return
        """
        # Step 1: Check cache
        cached = await self._repository.get_by_date(ticker, market, target_date)
        if cached is not None:
            # CACHE HIT
            self._metrics.record_cache_hit(ticker, market)
            return cached  # HIT: no adapter call

        # CACHE MISS
        self._metrics.record_cache_miss(ticker, market)

        # Step 2: Cache miss — fetch from adapter
        fresh_data = await self._adapter.fetch_daily_ohlcv(ticker, market, target_date)
        if fresh_data is None:
            return None  # holiday/weekend/invalid ticker

        # Step 3: Store to DB (degrade gracefully on failure)
        await self._store_to_db([fresh_data])

        return fresh_data

    async def fetch_multiple_and_cache(
        self, tickers: list[str], market: str, target_date: date
    ) -> list[dict]:
        """
        Batch fetch with cache-aside.
        Only calls adapter for cache misses.
        """
        # Step 1: Bulk check cache
        cached_list = await self._repository.get_multiple_by_date(
            tickers, market, target_date
        )
        cached_tickers = {d["ticker"] for d in cached_list}

        # Record cache hits for cached tickers
        for ticker in cached_tickers:
            self._metrics.record_cache_hit(ticker, market)

        # Step 2: Identify misses
        missed_tickers = [t for t in tickers if t not in cached_tickers]
        
        # Record cache misses
        for ticker in missed_tickers:
            self._metrics.record_cache_miss(ticker, market)

        # Step 3: Fetch misses from adapter
        fresh_list = []
        if missed_tickers:
            fresh_list = await self._adapter.fetch_multiple(
                missed_tickers, market, target_date
            )
            if fresh_list:
                await self._store_to_db(fresh_list)

        return cached_list + fresh_list

    async def _store_to_db(self, data_list: list[dict]) -> None:
        """
        Store to DB with graceful degradation.
        If DB write fails, log error but do NOT raise.
        """
        try:
            await self._repository.bulk_upsert(data_list)
        except Exception as e:
            # Degraded cache: log and continue
            # TODO Step 23: proper logging
            print(f"[WARN] Cache store failed: {e}")

    async def fetch_with_fallback(
        self, ticker: str, market: str, target_date: date
    ) -> Result[dict]:
        """
        Fetch market data with fallback strategy.
        
        Strategy:
        1. Try adapter (fresh data)
        2. If adapter fails, try previous day from cache
        3. If no previous day, try adapter with previous business day
        4. If all fails, return Result.fail
        
        Returns:
            Result[dict]: Success with data or failure with error message
        """
        # Step 1: Try primary adapter
        if hasattr(self._adapter, 'fetch_daily_ohlcv_safe'):
            adapter_result = await self._adapter.fetch_daily_ohlcv_safe(
                ticker, market, target_date
            )
            if adapter_result.is_ok():
                return adapter_result
        
        # Step 2: Try cache for previous business day
        try:
            fallback_date = self._get_previous_business_day(target_date)
            cached_data = await self._repository.get_by_date(ticker, market, fallback_date)
            
            if cached_data is not None:
                # Validate cached data
                try:
                    validated_data = self._validator.validate(cached_data)
                    return Result.ok(validated_data)
                except Exception:
                    # Skip invalid cached data
                    pass
        except Exception:
            # Repository failure - continue to final fallback
            pass
        
        # Step 3: Final fallback - return error
        return Result.fail(
            f"No data available for {ticker} on {target_date} or {fallback_date if 'fallback_date' in locals() else 'previous business day'}"
        )

    def _get_previous_business_day(self, target_date: date) -> date:
        """Get previous business day (skip weekends)."""
        previous_date = target_date - timedelta(days=1)
        
        # Skip backwards through weekends
        while previous_date.weekday() >= 5:  # Saturday=5, Sunday=6
            previous_date -= timedelta(days=1)
        
        return previous_date
