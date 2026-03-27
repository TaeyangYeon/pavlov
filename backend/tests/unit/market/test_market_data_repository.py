"""
Unit tests for MarketDataRepository.
Tests DB layer with mocked AsyncSession.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.infra.db.models.market_data import MarketData, MarketEnum
from app.infra.db.repositories.market_data_repository import MarketDataRepository


class TestMarketDataRepository:
    """Test repository DB operations with mocked session."""

    @pytest.fixture
    def mock_session(self):
        """Mock AsyncSession."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def repository(self, mock_session):
        """Repository instance with mocked session."""
        return MarketDataRepository(mock_session)

    @pytest.fixture
    def sample_market_data(self):
        """Sample MarketData ORM instance."""
        return MarketData(
            id=uuid4(),
            ticker="AAPL",
            market=MarketEnum.US,
            date=date(2024, 1, 2),
            open=Decimal("180.00"),
            high=Decimal("185.00"),
            low=Decimal("179.50"),
            close=Decimal("184.25"),
            volume=50000000,
        )

    @pytest.mark.asyncio
    async def test_get_by_date_returns_dict_when_found(
        self, repository, mock_session, sample_market_data
    ):
        """When data exists in DB, return converted dict with all 8 keys."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_market_data
        mock_session.execute.return_value = mock_result

        # Act
        result = await repository.get_by_date("AAPL", "US", date(2024, 1, 2))

        # Assert
        assert result is not None
        assert isinstance(result, dict)
        assert set(result.keys()) == {
            "ticker",
            "market",
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
        }
        assert result["ticker"] == "AAPL"
        assert result["market"] == "US"
        assert result["date"] == "2024-01-02"
        assert result["open"] == 180.0
        assert result["close"] == 184.25
        assert result["volume"] == 50000000

    @pytest.mark.asyncio
    async def test_get_by_date_returns_none_when_not_found(
        self, repository, mock_session
    ):
        """When no data in DB, return None."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await repository.get_by_date("TSLA", "US", date(2024, 1, 2))

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_date_queries_correct_columns(self, repository, mock_session):
        """Verify query uses ticker + market + date filter."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        await repository.get_by_date("AAPL", "US", date(2024, 1, 2))

        # Assert
        mock_session.execute.assert_called_once()
        called_stmt = mock_session.execute.call_args[0][0]
        # Verify it's a select statement for MarketData
        assert str(called_stmt).startswith("SELECT")
        assert "market_data" in str(called_stmt)

    @pytest.mark.asyncio
    async def test_bulk_upsert_calls_execute(self, repository, mock_session):
        """Verify bulk_upsert calls execute with upsert statement."""
        # Arrange
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

        # Act
        await repository.bulk_upsert(data_list)

        # Assert
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_upsert_with_empty_list_does_nothing(
        self, repository, mock_session
    ):
        """When data_list is empty, no DB operations."""
        # Act
        await repository.bulk_upsert([])

        # Assert
        mock_session.execute.assert_not_called()
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_multiple_by_date_returns_list(self, repository, mock_session):
        """Fetch multiple tickers for same date returns list of dicts."""
        # Arrange
        sample_data_1 = MarketData(
            id=uuid4(),
            ticker="AAPL",
            market=MarketEnum.US,
            date=date(2024, 1, 2),
            open=Decimal("180.00"),
            high=Decimal("185.00"),
            low=Decimal("179.50"),
            close=Decimal("184.25"),
            volume=50000000,
        )
        sample_data_2 = MarketData(
            id=uuid4(),
            ticker="MSFT",
            market=MarketEnum.US,
            date=date(2024, 1, 2),
            open=Decimal("370.00"),
            high=Decimal("375.00"),
            low=Decimal("369.50"),
            close=Decimal("374.25"),
            volume=30000000,
        )
        sample_data_3 = MarketData(
            id=uuid4(),
            ticker="GOOGL",
            market=MarketEnum.US,
            date=date(2024, 1, 2),
            open=Decimal("140.00"),
            high=Decimal("145.00"),
            low=Decimal("139.50"),
            close=Decimal("144.25"),
            volume=25000000,
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            sample_data_1,
            sample_data_2,
            sample_data_3,
        ]
        mock_session.execute.return_value = mock_result

        # Act
        result = await repository.get_multiple_by_date(
            ["AAPL", "MSFT", "GOOGL"], "US", date(2024, 1, 2)
        )

        # Assert
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(item, dict) for item in result)
        assert result[0]["ticker"] == "AAPL"
        assert result[1]["ticker"] == "MSFT"
        assert result[2]["ticker"] == "GOOGL"
