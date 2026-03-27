"""
MarketDataService implementation.
Orchestrates market data fetching with cache-aside pattern.
Single responsibility: cache logic only.
"""

from datetime import date

from app.domain.market.interfaces import MarketDataPort
from app.infra.db.repositories.market_data_repository import MarketDataRepository


class MarketDataService:
    """
    Orchestrates market data fetching with cache-aside pattern.
    Single responsibility: cache logic only.
    Depends on abstractions (MarketDataPort, not concrete adapters).
    """

    def __init__(self, adapter: MarketDataPort, repository: MarketDataRepository):
        self._adapter = adapter
        self._repository = repository

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
            return cached  # HIT: no adapter call

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

        # Step 2: Identify misses
        missed_tickers = [t for t in tickers if t not in cached_tickers]

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
