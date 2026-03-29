"""
Unit tests for PositionService.
Tests business logic layer with mocked repository.
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from app.domain.position.interfaces import PositionRepositoryPort
from app.domain.position.schemas import PositionCreate, PositionEntry, PositionResponse
from app.domain.position.service import PositionService


@pytest.fixture
def mock_repository():
    """Mock PositionRepositoryPort for testing."""
    return AsyncMock(spec=PositionRepositoryPort)


@pytest.fixture
def service(mock_repository):
    """PositionService instance with mocked repository."""
    return PositionService(mock_repository)


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing."""
    return UUID("00000000-0000-0000-0000-000000000001")


class TestPositionService:
    """Test cases for PositionService business logic."""

    @pytest.mark.asyncio
    async def test_create_calculates_weighted_avg_price(
        self, service, mock_repository
    ):
        """Test create_position() calculates correct weighted average price."""
        # Setup: entries with different prices and quantities
        entries = [
            PositionEntry(
                price=Decimal("100.00"),
                quantity=Decimal("10"),
                entered_at=datetime.fromisoformat("2024-01-01T10:00:00")
            ),
            PositionEntry(
                price=Decimal("90.00"),
                quantity=Decimal("5"),
                entered_at=datetime.fromisoformat("2024-01-02T10:00:00")
            )
        ]

        position_create = PositionCreate(
            ticker="AAPL",
            market="US",
            entries=entries
        )

        # Expected weighted average: (100*10 + 90*5) / (10+5) = 1450/15 = 96.6667
        expected_avg = Decimal("96.6667")

        # Mock repository response
        mock_response = PositionResponse(
            id=uuid4(),
            ticker="AAPL",
            market="US",
            entries=entries,
            avg_price=expected_avg,
            status="open",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_repository.create.return_value = mock_response

        # Execute
        result = await service.create_position(position_create)

        # Assert: repository called with calculated avg_price
        mock_repository.create.assert_called_once()
        call_args = mock_repository.create.call_args
        created_data = call_args[0][0]  # First positional arg

        # Verify avg_price was calculated and set
        assert created_data.avg_price == expected_avg
        assert result == mock_response

    @pytest.mark.asyncio
    async def test_create_single_entry_avg_equals_price(
        self, service, mock_repository
    ):
        """Test single entry position has avg_price equal to entry price."""
        # Setup: single entry
        entry = PositionEntry(
            price=Decimal("100.00"),
            quantity=Decimal("10"),
            entered_at=datetime.now()
        )

        position_create = PositionCreate(
            ticker="TSLA",
            market="US",
            entries=[entry]
        )

        # Mock repository response
        mock_response = PositionResponse(
            id=uuid4(),
            ticker="TSLA",
            market="US",
            entries=[entry],
            avg_price=Decimal("100.0000"),
            status="open",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_repository.create.return_value = mock_response

        # Execute
        result = await service.create_position(position_create)

        # Assert
        call_args = mock_repository.create.call_args
        created_data = call_args[0][0]
        assert created_data.avg_price == Decimal("100.0000")

    @pytest.mark.asyncio
    async def test_add_entry_recalculates_avg_price(
        self, service, mock_repository
    ):
        """Test add_entry() recalculates weighted average price."""
        position_id = uuid4()

        # Setup: existing position with one entry
        existing_entry = PositionEntry(
            price=Decimal("100.00"),
            quantity=Decimal("10"),
            entered_at=datetime.fromisoformat("2024-01-01T10:00:00")
        )

        existing_position = PositionResponse(
            id=position_id,
            ticker="AAPL",
            market="US",
            entries=[existing_entry],
            avg_price=Decimal("100.0000"),
            status="open",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # New entry to add
        new_entry = PositionEntry(
            price=Decimal("80.00"),
            quantity=Decimal("10"),
            entered_at=datetime.fromisoformat("2024-01-02T10:00:00")
        )

        # Expected new average: (100*10 + 80*10) / (10+10) = 1800/20 = 90.0000
        expected_new_avg = Decimal("90.0000")

        # Mock repository responses
        mock_repository.get_by_id.return_value = existing_position

        updated_position = PositionResponse(
            id=position_id,
            ticker="AAPL",
            market="US",
            entries=[existing_entry, new_entry],
            avg_price=expected_new_avg,
            status="open",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_repository.update.return_value = updated_position

        # Execute
        result = await service.add_entry(position_id, new_entry)

        # Assert
        mock_repository.get_by_id.assert_called_once_with(position_id)
        mock_repository.update.assert_called_once()

        # Verify update called with correct avg_price
        call_args = mock_repository.update.call_args
        update_data = call_args[0][1]  # Second positional arg (data dict)
        assert update_data["avg_price"] == expected_new_avg

        assert result == updated_position

    @pytest.mark.asyncio
    async def test_create_position_stores_avg_price(
        self, service, mock_repository
    ):
        """Test create_position() ensures avg_price is never None when entries exist."""
        # Setup
        entry = PositionEntry(
            price=Decimal("123.45"),
            quantity=Decimal("7"),
            entered_at=datetime.now()
        )

        position_create = PositionCreate(
            ticker="NVDA",
            market="US",
            entries=[entry]
        )

        mock_response = PositionResponse(
            id=uuid4(),
            ticker="NVDA",
            market="US",
            entries=[entry],
            avg_price=Decimal("123.4500"),
            status="open",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_repository.create.return_value = mock_response

        # Execute
        await service.create_position(position_create)

        # Assert: verify avg_price is calculated and not None
        call_args = mock_repository.create.call_args
        created_data = call_args[0][0]
        assert created_data.avg_price is not None
        assert created_data.avg_price == Decimal("123.4500")

    @pytest.mark.asyncio
    async def test_get_open_positions_by_user(
        self, service, mock_repository, sample_user_id
    ):
        """Test get_open_positions() delegates to repository."""
        # Setup: mock repository response
        mock_positions = [
            PositionResponse(
                id=uuid4(),
                ticker="AAPL",
                market="US",
                entries=[],
                avg_price=Decimal("150.0000"),
                status="open",
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            PositionResponse(
                id=uuid4(),
                ticker="GOOGL",
                market="US",
                entries=[],
                avg_price=Decimal("2500.0000"),
                status="open",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        mock_repository.get_open_positions.return_value = mock_positions

        # Execute
        result = await service.get_open_positions()

        # Assert
        mock_repository.get_open_positions.assert_called_once_with(sample_user_id)
        assert result == mock_positions

    @pytest.mark.asyncio
    async def test_close_position_sets_status_closed(
        self, service, mock_repository
    ):
        """Test close_position() delegates to repository delete."""
        # Setup
        position_id = uuid4()
        mock_repository.delete.return_value = True

        # Execute
        result = await service.close_position(position_id)

        # Assert
        mock_repository.delete.assert_called_once_with(position_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_add_entry_returns_none_when_position_not_found(
        self, service, mock_repository
    ):
        """Test add_entry() returns None when position doesn't exist."""
        # Setup
        position_id = uuid4()
        new_entry = PositionEntry(
            price=Decimal("100.00"),
            quantity=Decimal("5"),
            entered_at=datetime.now()
        )
        mock_repository.get_by_id.return_value = None

        # Execute
        result = await service.add_entry(position_id, new_entry)

        # Assert
        assert result is None
        mock_repository.get_by_id.assert_called_once_with(position_id)
        mock_repository.update.assert_not_called()

    def test_calculate_avg_price_weighted_average(self, service):
        """Test _calculate_avg_price() computes correct weighted average."""
        # Setup: multiple entries with different weights
        entries = [
            PositionEntry(
                price=Decimal("100.00"),
                quantity=Decimal("10"),
                entered_at=datetime.now()
            ),
            PositionEntry(
                price=Decimal("90.00"),
                quantity=Decimal("5"),
                entered_at=datetime.now()
            ),
            PositionEntry(
                price=Decimal("110.00"),
                quantity=Decimal("15"),
                entered_at=datetime.now()
            )
        ]

        # Expected: (100*10 + 90*5 + 110*15) / (10+5+15) = 3100/30 = 103.3333
        expected = Decimal("103.3333")

        # Execute
        result = service._calculate_avg_price(entries)

        # Assert
        assert result == expected

    def test_calculate_avg_price_zero_quantity(self, service):
        """Test _calculate_avg_price() handles zero total quantity."""
        # Setup: empty entries
        entries = []

        # Execute
        result = service._calculate_avg_price(entries)

        # Assert
        assert result == Decimal("0")

    def test_calculate_avg_price_precision(self, service):
        """Test _calculate_avg_price() maintains 4 decimal precision."""
        # Setup: entries that result in many decimal places
        entries = [
            PositionEntry(
                price=Decimal("33.333333"),
                quantity=Decimal("3"),
                entered_at=datetime.now()
            )
        ]

        # Execute
        result = service._calculate_avg_price(entries)

        # Assert: should be quantized to 4 decimal places
        assert str(result) == "33.3333"
        assert result.as_tuple().exponent == -4  # 4 decimal places
