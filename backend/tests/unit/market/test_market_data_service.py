"""
Unit tests for MarketDataService.
Tests cache-aside logic with mocked repository and adapter.
"""

from datetime import date
from unittest.mock import AsyncMock

import pytest
from app.domain.market.service import MarketDataService


class TestMarketDataService:
    """Test service cache logic with mocked dependencies."""

    @pytest.fixture
    def mock_adapter(self):
        """Mock MarketDataPort adapter."""
        return AsyncMock()

    @pytest.fixture
    def mock_repository(self):
        """Mock MarketDataRepository."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_adapter, mock_repository):
        """Service instance with mocked dependencies."""
        return MarketDataService(mock_adapter, mock_repository)

    @pytest.fixture
    def sample_cached_data(self):
        """Sample cached data dict."""
        return {
            "ticker": "AAPL",
            "market": "US",
            "date": "2024-01-02",
            "open": 180.0,
            "high": 185.0,
            "low": 179.5,
            "close": 184.25,
            "volume": 50000000,
        }

    @pytest.mark.asyncio
    async def test_fetch_and_cache_returns_cached_on_hit(
        self, service, mock_adapter, mock_repository, sample_cached_data
    ):
        """Cache HIT: return cached data without calling adapter."""
        # Arrange - repository returns cached data (cache HIT)
        mock_repository.get_by_date.return_value = sample_cached_data

        # Act
        result = await service.fetch_and_cache("AAPL", "US", date(2024, 1, 2))

        # Assert
        assert result == sample_cached_data
        # Adapter should NOT be called on cache hit
        mock_adapter.fetch_daily_ohlcv.assert_not_called()
        # Repository checked for cache
        mock_repository.get_by_date.assert_called_once_with(
            "AAPL", "US", date(2024, 1, 2)
        )

    @pytest.mark.asyncio
    async def test_fetch_and_cache_calls_adapter_on_miss(
        self, service, mock_adapter, mock_repository, sample_cached_data
    ):
        """Cache MISS: call adapter exactly once."""
        # Arrange - repository returns None (cache MISS)
        mock_repository.get_by_date.return_value = None
        mock_adapter.fetch_daily_ohlcv.return_value = sample_cached_data

        # Act
        result = await service.fetch_and_cache("AAPL", "US", date(2024, 1, 2))

        # Assert
        assert result == sample_cached_data
        # Adapter called exactly once on cache miss
        mock_adapter.fetch_daily_ohlcv.assert_called_once_with(
            "AAPL", "US", date(2024, 1, 2)
        )

    @pytest.mark.asyncio
    async def test_fetch_and_cache_stores_to_db_on_miss(
        self, service, mock_adapter, mock_repository, sample_cached_data
    ):
        """Cache MISS: store fetched data to DB."""
        # Arrange
        mock_repository.get_by_date.return_value = None
        mock_adapter.fetch_daily_ohlcv.return_value = sample_cached_data

        # Act
        await service.fetch_and_cache("AAPL", "US", date(2024, 1, 2))

        # Assert - data stored to repository
        mock_repository.bulk_upsert.assert_called_once_with([sample_cached_data])

    @pytest.mark.asyncio
    async def test_fetch_and_cache_returns_data_even_if_store_fails(
        self, service, mock_adapter, mock_repository, sample_cached_data
    ):
        """Degraded cache: store fails but data still returned."""
        # Arrange
        mock_repository.get_by_date.return_value = None
        mock_adapter.fetch_daily_ohlcv.return_value = sample_cached_data
        # Repository store fails
        mock_repository.bulk_upsert.side_effect = Exception("DB connection lost")

        # Act - should NOT raise exception
        result = await service.fetch_and_cache("AAPL", "US", date(2024, 1, 2))

        # Assert
        assert result == sample_cached_data  # Data still returned
        # Store was attempted but failed
        mock_repository.bulk_upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_and_cache_returns_none_when_adapter_returns_none(
        self, service, mock_adapter, mock_repository
    ):
        """When adapter returns None (holiday/invalid), return None."""
        # Arrange
        mock_repository.get_by_date.return_value = None
        mock_adapter.fetch_daily_ohlcv.return_value = None  # Holiday/weekend

        # Act
        result = await service.fetch_and_cache("AAPL", "US", date(2024, 1, 1))

        # Assert
        assert result is None
        # Store should not be called when adapter returns None
        mock_repository.bulk_upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_multiple_and_cache_returns_list(
        self, service, mock_adapter, mock_repository
    ):
        """Batch fetch: 2 cache hits + 1 miss = adapter called once."""
        # Arrange
        cached_aapl = {
            "ticker": "AAPL",
            "market": "US",
            "date": "2024-01-02",
            "open": 180.0,
            "high": 185.0,
            "low": 179.5,
            "close": 184.25,
            "volume": 50000000,
        }
        cached_msft = {
            "ticker": "MSFT",
            "market": "US",
            "date": "2024-01-02",
            "open": 370.0,
            "high": 375.0,
            "low": 369.5,
            "close": 374.25,
            "volume": 30000000,
        }
        fresh_googl = {
            "ticker": "GOOGL",
            "market": "US",
            "date": "2024-01-02",
            "open": 140.0,
            "high": 145.0,
            "low": 139.5,
            "close": 144.25,
            "volume": 25000000,
        }

        # Repository returns 2 cached items (AAPL, MSFT hit; GOOGL miss)
        mock_repository.get_multiple_by_date.return_value = [cached_aapl, cached_msft]
        # Adapter fetches only the missed ticker (GOOGL)
        mock_adapter.fetch_multiple.return_value = [fresh_googl]

        # Act
        result = await service.fetch_multiple_and_cache(
            ["AAPL", "MSFT", "GOOGL"], "US", date(2024, 1, 2)
        )

        # Assert
        assert len(result) == 3
        assert cached_aapl in result
        assert cached_msft in result
        assert fresh_googl in result
        # Adapter called with only the missed ticker
        mock_adapter.fetch_multiple.assert_called_once_with(
            ["GOOGL"], "US", date(2024, 1, 2)
        )
        # Fresh data stored to DB
        mock_repository.bulk_upsert.assert_called_once_with([fresh_googl])

    @pytest.mark.asyncio
    async def test_fetch_multiple_skips_none_results(
        self, service, mock_adapter, mock_repository
    ):
        """When adapter returns None for a ticker, exclude from results."""
        # Arrange
        # No cache hits
        mock_repository.get_multiple_by_date.return_value = []
        # Adapter returns data for AAPL but None for invalid ticker
        mock_adapter.fetch_multiple.return_value = [
            {
                "ticker": "AAPL",
                "market": "US",
                "date": "2024-01-02",
                "open": 180.0,
                "high": 185.0,
                "low": 179.5,
                "close": 184.25,
                "volume": 50000000,
            }
            # INVALID ticker returns None (excluded by adapter)
        ]

        # Act
        result = await service.fetch_multiple_and_cache(
            ["AAPL", "INVALID"], "US", date(2024, 1, 2)
        )

        # Assert
        assert len(result) == 1  # Only AAPL, INVALID excluded
        assert result[0]["ticker"] == "AAPL"
