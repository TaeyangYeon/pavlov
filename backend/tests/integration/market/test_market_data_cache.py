"""
Integration tests for market data caching.
Tests real cache-aside pattern with test database.
"""

from datetime import date

import pytest
from app.domain.market.service import MarketDataService
from app.infra.db.repositories.market_data_repository import MarketDataRepository


class MockMarketAdapter:
    """Simple mock adapter for integration tests."""

    def __init__(self):
        self.call_count = 0
        self.fetch_responses = {}
        self.fetch_multiple_responses = {}

    async def fetch_daily_ohlcv(
        self, ticker: str, market: str, target_date: date
    ) -> dict | None:
        self.call_count += 1
        key = (ticker, market, target_date)
        return self.fetch_responses.get(key)

    async def fetch_multiple(
        self, tickers: list[str], market: str, target_date: date
    ) -> list[dict]:
        self.call_count += 1
        key = (tuple(tickers), market, target_date)
        return self.fetch_multiple_responses.get(key, [])

    async def is_market_open(self, market: str) -> bool:
        return True


@pytest.mark.integration
class TestMarketDataCache:
    """Integration tests for market data cache-aside pattern."""

    @pytest.fixture
    def mock_adapter(self):
        """Mock adapter with configurable responses."""
        adapter = MockMarketAdapter()
        adapter.fetch_responses = {
            ("AAPL", "US", date(2024, 1, 2)): {
                "ticker": "AAPL",
                "market": "US",
                "date": "2024-01-02",
                "open": 180.0,
                "high": 185.0,
                "low": 179.5,
                "close": 184.25,
                "volume": 50000000,
            }
        }
        return adapter

    @pytest.fixture
    def service(self, db_session, mock_adapter):
        """Service instance with real DB session and mock adapter."""
        repository = MarketDataRepository(db_session)
        return MarketDataService(mock_adapter, repository)

    @pytest.mark.asyncio
    async def test_cache_miss_then_hit(self, service, mock_adapter):
        """
        Full cache-aside flow with real test DB.
        First call: miss → fetch mock data → store.
        Second call: hit → return from DB.
        """
        target_date = date(2024, 1, 2)

        # First call: cache miss
        result1 = await service.fetch_and_cache("AAPL", "US", target_date)
        assert result1 is not None
        assert result1["ticker"] == "AAPL"
        assert result1["close"] == 184.25
        assert mock_adapter.call_count == 1

        # Second call: cache hit (adapter should NOT be called again)
        result2 = await service.fetch_and_cache("AAPL", "US", target_date)
        assert result2 == result1
        assert mock_adapter.call_count == 1  # NOT called again

    @pytest.mark.asyncio
    async def test_bulk_upsert_no_duplicate(self, db_session):
        """Inserting same ticker/market/date twice → only 1 row."""
        repository = MarketDataRepository(db_session)

        # Same data twice
        data_list = [
            {
                "ticker": "AAPL",
                "market": "US",
                "date": date(2024, 1, 2),
                "open": 180.0,
                "high": 185.0,
                "low": 179.5,
                "close": 184.25,
                "volume": 50000000,
            }
        ]

        # Insert twice
        await repository.bulk_upsert(data_list)
        await repository.bulk_upsert(data_list)

        # Should have only one row
        result = await repository.get_by_date("AAPL", "US", date(2024, 1, 2))
        assert result is not None
        assert result["close"] == 184.25

    @pytest.mark.asyncio
    async def test_cache_miss_with_holiday_returns_none(self, service, mock_adapter):
        """When adapter returns None (holiday), service returns None."""
        # Mock adapter returns None for this date (holiday)
        mock_adapter.fetch_responses[("AAPL", "US", date(2024, 1, 1))] = None

        result = await service.fetch_and_cache("AAPL", "US", date(2024, 1, 1))
        assert result is None
        assert mock_adapter.call_count == 1

    @pytest.mark.asyncio
    async def test_multiple_fetch_with_partial_cache_hit(self, service, mock_adapter):
        """Batch fetch: some cached, some missed."""
        target_date = date(2024, 1, 2)

        # Pre-populate cache with AAPL only
        await service.fetch_and_cache("AAPL", "US", target_date)
        initial_call_count = mock_adapter.call_count

        # Configure mock for MSFT (not cached)
        mock_adapter.fetch_multiple_responses[(("MSFT",), "US", target_date)] = [
            {
                "ticker": "MSFT",
                "market": "US",
                "date": "2024-01-02",
                "open": 370.0,
                "high": 375.0,
                "low": 369.5,
                "close": 374.25,
                "volume": 30000000,
            }
        ]

        # Fetch both tickers
        results = await service.fetch_multiple_and_cache(
            ["AAPL", "MSFT"], "US", target_date
        )

        # Should get both results
        assert len(results) == 2
        tickers = {r["ticker"] for r in results}
        assert tickers == {"AAPL", "MSFT"}

        # Adapter called only once for MSFT (AAPL was cached)
        assert mock_adapter.call_count == initial_call_count + 1
