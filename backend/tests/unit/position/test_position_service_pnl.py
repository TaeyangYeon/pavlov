"""
Unit tests for PositionService PnL extensions.
Tests integration between service layer and PnL calculator.
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.domain.position.exceptions import InvalidPriceError, PositionNotFoundError
from app.domain.position.interfaces import PositionRepositoryPort
from app.domain.position.pnl_calculator import PnLCalculator
from app.domain.position.schemas import (
    PnLResult,
    PositionEntry,
    PositionResponse,
    PositionWithPnL,
)
from app.domain.position.service import PositionService


@pytest.fixture
def mock_repository():
    """Mock PositionRepositoryPort for testing."""
    return AsyncMock(spec=PositionRepositoryPort)


@pytest.fixture
def mock_calculator():
    """Mock PnLCalculator for testing."""
    return MagicMock(spec=PnLCalculator)


@pytest.fixture
def service_with_mocks(mock_repository, mock_calculator):
    """PositionService instance with mocked dependencies."""
    service = PositionService(mock_repository, calculator=mock_calculator)
    return service


@pytest.fixture
def sample_position():
    """Sample position for testing."""
    return PositionResponse(
        id=uuid4(),
        ticker="AAPL",
        market="US",
        entries=[
            PositionEntry(
                price=Decimal("100.00"),
                quantity=Decimal("10"),
                entered_at=datetime.fromisoformat("2024-01-01T10:00:00")
            )
        ],
        avg_price=Decimal("100.0000"),
        status="open",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def sample_pnl_result():
    """Sample PnL calculation result."""
    return PnLResult(
        unrealized_pnl=Decimal("200.0000"),
        unrealized_pnl_percent=Decimal("20.0000"),
        realized_pnl=Decimal("0.0000"),
        total_pnl=Decimal("200.0000")
    )


class TestPositionServicePnL:
    """Test cases for PositionService PnL functionality."""

    @pytest.mark.asyncio
    async def test_get_position_with_pnl_returns_enriched_data(
        self, service_with_mocks, mock_repository, mock_calculator,
        sample_position, sample_pnl_result
    ):
        """Test get_position_with_pnl() returns position with calculated PnL."""
        # Setup mocks
        position_id = sample_position.id
        current_price = Decimal("120.00")

        mock_repository.get_by_id.return_value = sample_position
        mock_calculator.calculate_unrealized.return_value = sample_pnl_result

        # Execute
        result = await service_with_mocks.get_position_with_pnl(
            position_id, current_price
        )

        # Assert
        assert isinstance(result, PositionWithPnL)
        assert result.id == position_id
        assert result.ticker == "AAPL"
        assert result.current_price == current_price
        assert result.unrealized_pnl == Decimal("200.0000")
        assert result.unrealized_pnl_percent == Decimal("20.0000")
        assert result.realized_pnl == Decimal("0.0000")
        assert result.total_pnl == Decimal("200.0000")

        mock_repository.get_by_id.assert_called_once_with(position_id)
        mock_calculator.calculate_unrealized.assert_called_once_with(
            sample_position, current_price
        )

    @pytest.mark.asyncio
    async def test_get_position_with_pnl_raises_when_not_found(
        self, service_with_mocks, mock_repository
    ):
        """Test get_position_with_pnl() raises exception when position not found."""
        # Setup: repository returns None
        position_id = uuid4()
        mock_repository.get_by_id.return_value = None

        # Execute & Assert
        with pytest.raises(PositionNotFoundError, match=f"Position {position_id} not found"):
            await service_with_mocks.get_position_with_pnl(
                position_id, Decimal("120.00")
            )

        mock_repository.get_by_id.assert_called_once_with(position_id)

    @pytest.mark.asyncio
    async def test_get_all_positions_with_pnl_returns_list(
        self, service_with_mocks, mock_repository, mock_calculator
    ):
        """Test get_all_positions_with_pnl() returns all positions with PnL."""
        # Setup: mock 3 positions
        positions = []
        pnl_results = []
        for i in range(3):
            position = PositionResponse(
                id=uuid4(),
                ticker=f"STOCK{i}",
                market="US",
                entries=[
                    PositionEntry(
                        price=Decimal(f"{100 + i}.00"),
                        quantity=Decimal("10"),
                        entered_at=datetime.now()
                    )
                ],
                avg_price=Decimal(f"{100 + i}.0000"),
                status="open",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            pnl_result = PnLResult(
                unrealized_pnl=Decimal(f"{10 * i}.0000"),
                unrealized_pnl_percent=Decimal(f"{i}.0000"),
                realized_pnl=Decimal("0.0000"),
                total_pnl=Decimal(f"{10 * i}.0000")
            )
            positions.append(position)
            pnl_results.append(pnl_result)

        current_price = Decimal("120.00")
        mock_repository.get_open_positions.return_value = positions
        mock_calculator.calculate_unrealized.side_effect = pnl_results

        # Execute
        result = await service_with_mocks.get_all_positions_with_pnl(current_price)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(p, PositionWithPnL) for p in result)

        # Verify each position has correct PnL data
        for i, position_with_pnl in enumerate(result):
            assert position_with_pnl.ticker == f"STOCK{i}"
            assert position_with_pnl.current_price == current_price
            assert position_with_pnl.unrealized_pnl == Decimal(f"{10 * i}.0000")
            assert position_with_pnl.total_pnl == Decimal(f"{10 * i}.0000")

        mock_repository.get_open_positions.assert_called_once()
        assert mock_calculator.calculate_unrealized.call_count == 3

    @pytest.mark.asyncio
    async def test_get_all_positions_with_pnl_empty_list(
        self, service_with_mocks, mock_repository
    ):
        """Test get_all_positions_with_pnl() handles empty positions list."""
        # Setup: no positions
        mock_repository.get_open_positions.return_value = []

        # Execute
        result = await service_with_mocks.get_all_positions_with_pnl(Decimal("120.00"))

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

        mock_repository.get_open_positions.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_position_with_pnl_preserves_all_fields(
        self, service_with_mocks, mock_repository, mock_calculator,
        sample_position, sample_pnl_result
    ):
        """Test get_position_with_pnl() preserves all original position fields."""
        # Setup
        position_id = sample_position.id
        current_price = Decimal("120.00")

        mock_repository.get_by_id.return_value = sample_position
        mock_calculator.calculate_unrealized.return_value = sample_pnl_result

        # Execute
        result = await service_with_mocks.get_position_with_pnl(
            position_id, current_price
        )

        # Assert: all original fields preserved
        assert result.id == sample_position.id
        assert result.ticker == sample_position.ticker
        assert result.market == sample_position.market
        assert result.entries == sample_position.entries
        assert result.avg_price == sample_position.avg_price
        assert result.status == sample_position.status
        assert result.created_at == sample_position.created_at
        assert result.updated_at == sample_position.updated_at

        # Assert: PnL fields added
        assert result.current_price == current_price
        assert result.unrealized_pnl == sample_pnl_result.unrealized_pnl
        assert result.unrealized_pnl_percent == sample_pnl_result.unrealized_pnl_percent
        assert result.realized_pnl == sample_pnl_result.realized_pnl
        assert result.total_pnl == sample_pnl_result.total_pnl

    @pytest.mark.asyncio
    async def test_get_position_with_pnl_handles_calculator_exceptions(
        self, service_with_mocks, mock_repository, mock_calculator, sample_position
    ):
        """Test get_position_with_pnl() propagates calculator exceptions."""
        # Setup: calculator raises exception
        position_id = sample_position.id
        current_price = Decimal("-10.00")  # Invalid price

        mock_repository.get_by_id.return_value = sample_position
        mock_calculator.calculate_unrealized.side_effect = InvalidPriceError("Current price must be positive")

        # Execute & Assert
        with pytest.raises(InvalidPriceError, match="Current price must be positive"):
            await service_with_mocks.get_position_with_pnl(position_id, current_price)

        mock_repository.get_by_id.assert_called_once_with(position_id)
        mock_calculator.calculate_unrealized.assert_called_once_with(
            sample_position, current_price
        )

    def test_service_has_pnl_calculator_attribute(self, mock_repository):
        """Test that PositionService has a PnLCalculator instance."""
        service = PositionService(mock_repository)

        # The service should either have a calculator or create one
        assert hasattr(service, '_calculator')
        # The calculator should be set during service initialization or lazily

    @pytest.mark.asyncio
    async def test_get_all_positions_with_pnl_uses_stub_user_id(
        self, service_with_mocks, mock_repository
    ):
        """Test get_all_positions_with_pnl() uses the stub user ID."""
        # Setup
        mock_repository.get_open_positions.return_value = []

        # Execute
        await service_with_mocks.get_all_positions_with_pnl(Decimal("120.00"))

        # Assert: called with the stub user ID
        from app.domain.position.service import STUB_USER_ID
        mock_repository.get_open_positions.assert_called_once_with(STUB_USER_ID)
