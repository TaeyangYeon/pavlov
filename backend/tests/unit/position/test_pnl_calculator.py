"""
Unit tests for PnLCalculator.
Tests exact known-value calculations with Decimal precision.
"""

from datetime import datetime
from decimal import Decimal

import pytest
from app.domain.position.exceptions import InvalidPriceError
from app.domain.position.pnl_calculator import PnLCalculator
from app.domain.position.schemas import PositionEntry, PositionResponse


@pytest.fixture
def calculator():
    """PnLCalculator instance for testing."""
    return PnLCalculator()


@pytest.fixture
def sample_position():
    """Sample position for testing."""
    return PositionResponse(
        id="00000000-0000-0000-0000-000000000001",
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


class TestPnLCalculator:
    """Test cases for PnL calculation engine."""

    def test_calculate_unrealized_positive_gain(self, calculator, sample_position):
        """Test unrealized P&L calculation for positive gain."""
        # Position: 10 shares @ $100.00 avg = $1000 invested
        # Current: $120.00 per share = $1200 value
        # Expected unrealized P&L: $200 (20%)
        current_price = Decimal("120.00")

        result = calculator.calculate_unrealized(sample_position, current_price)

        assert result.unrealized_pnl == Decimal("200.0000")
        assert result.unrealized_pnl_percent == Decimal("20.0000")
        assert result.realized_pnl == Decimal("0.0000")
        assert result.total_pnl == Decimal("200.0000")

    def test_calculate_unrealized_negative_loss(self, calculator, sample_position):
        """Test unrealized P&L calculation for negative loss."""
        # Position: 10 shares @ $100.00 avg = $1000 invested
        # Current: $85.00 per share = $850 value
        # Expected unrealized P&L: -$150 (-15%)
        current_price = Decimal("85.00")

        result = calculator.calculate_unrealized(sample_position, current_price)

        assert result.unrealized_pnl == Decimal("-150.0000")
        assert result.unrealized_pnl_percent == Decimal("-15.0000")
        assert result.realized_pnl == Decimal("0.0000")
        assert result.total_pnl == Decimal("-150.0000")

    def test_calculate_unrealized_zero_gain_loss(self, calculator, sample_position):
        """Test unrealized P&L calculation when price equals avg price."""
        # Position: 10 shares @ $100.00 avg = $1000 invested
        # Current: $100.00 per share = $1000 value
        # Expected unrealized P&L: $0 (0%)
        current_price = Decimal("100.00")

        result = calculator.calculate_unrealized(sample_position, current_price)

        assert result.unrealized_pnl == Decimal("0.0000")
        assert result.unrealized_pnl_percent == Decimal("0.0000")
        assert result.realized_pnl == Decimal("0.0000")
        assert result.total_pnl == Decimal("0.0000")

    def test_calculate_unrealized_multi_entry_weighted_avg(self, calculator):
        """Test unrealized P&L with multiple entries (weighted average)."""
        # Entry 1: 10 shares @ $100.00 = $1000
        # Entry 2: 5 shares @ $90.00 = $450
        # Total: 15 shares, $1450 invested, avg = $96.6667
        # Current: $110.00 per share = $1650 value
        # Expected unrealized P&L: $200 (13.7931%)
        position = PositionResponse(
            id="00000000-0000-0000-0000-000000000001",
            ticker="AAPL",
            market="US",
            entries=[
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
            ],
            avg_price=Decimal("96.6667"),  # (100*10 + 90*5) / 15
            status="open",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        current_price = Decimal("110.00")

        result = calculator.calculate_unrealized(position, current_price)

        # Current value: 15 * $110 = $1650
        # Cost basis: 15 * $96.6667 = $1450.0005
        # P&L: $1650 - $1450.0005 = $199.9995
        # Percent: (110 - 96.6667) / 96.6667 * 100 = 13.7931%
        assert result.unrealized_pnl == Decimal("199.9995")
        assert result.unrealized_pnl_percent == Decimal("13.7931")
        assert result.realized_pnl == Decimal("0.0000")
        assert result.total_pnl == Decimal("199.9995")

    def test_calculate_unrealized_precision_handling(self, calculator):
        """Test P&L calculation maintains 4-decimal precision."""
        # Test with prices that create many decimal places
        position = PositionResponse(
            id="00000000-0000-0000-0000-000000000001",
            ticker="TEST",
            market="US",
            entries=[
                PositionEntry(
                    price=Decimal("33.333333"),
                    quantity=Decimal("3"),
                    entered_at=datetime.now()
                )
            ],
            avg_price=Decimal("33.3333"),
            status="open",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        current_price = Decimal("36.666666")

        result = calculator.calculate_unrealized(position, current_price)

        # All results should be quantized to 4 decimal places
        assert result.unrealized_pnl.as_tuple().exponent == -4
        assert result.unrealized_pnl_percent.as_tuple().exponent == -4
        assert result.realized_pnl.as_tuple().exponent == -4
        assert result.total_pnl.as_tuple().exponent == -4

    def test_calculate_realized_with_partial_sale(self, calculator):
        """Test realized P&L calculation with partial position sale."""
        # Original: 10 shares @ $100.00
        # Sold: 3 shares @ $120.00
        # Remaining: 7 shares @ $100.00 avg
        # Expected realized P&L: 3 * ($120 - $100) = $60
        original_position = PositionResponse(
            id="00000000-0000-0000-0000-000000000001",
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

        remaining_position = PositionResponse(
            id="00000000-0000-0000-0000-000000000001",
            ticker="AAPL",
            market="US",
            entries=[
                PositionEntry(
                    price=Decimal("100.00"),
                    quantity=Decimal("7"),
                    entered_at=datetime.fromisoformat("2024-01-01T10:00:00")
                )
            ],
            avg_price=Decimal("100.0000"),
            status="open",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        sale_price = Decimal("120.00")

        result = calculator.calculate_realized(
            original_position, remaining_position, sale_price
        )

        assert result.unrealized_pnl == Decimal("0.0000")
        assert result.unrealized_pnl_percent == Decimal("0.0000")
        assert result.realized_pnl == Decimal("60.0000")
        assert result.total_pnl == Decimal("60.0000")

    def test_calculate_realized_complete_sale(self, calculator):
        """Test realized P&L calculation with complete position sale."""
        # Original: 10 shares @ $100.00
        # Sold: all 10 shares @ $90.00
        # Expected realized P&L: 10 * ($90 - $100) = -$100
        original_position = PositionResponse(
            id="00000000-0000-0000-0000-000000000001",
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
            status="closed",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # No remaining position (None or empty)
        remaining_position = None
        sale_price = Decimal("90.00")

        result = calculator.calculate_realized(
            original_position, remaining_position, sale_price
        )

        assert result.unrealized_pnl == Decimal("0.0000")
        assert result.unrealized_pnl_percent == Decimal("0.0000")
        assert result.realized_pnl == Decimal("-100.0000")
        assert result.total_pnl == Decimal("-100.0000")

    def test_calculate_realized_zero_quantity_sold(self, calculator, sample_position):
        """Test realized P&L when no shares were sold."""
        # Same position before and after (no sale)
        result = calculator.calculate_realized(
            sample_position, sample_position, Decimal("120.00")
        )

        assert result.unrealized_pnl == Decimal("0.0000")
        assert result.unrealized_pnl_percent == Decimal("0.0000")
        assert result.realized_pnl == Decimal("0.0000")
        assert result.total_pnl == Decimal("0.0000")

    def test_invalid_price_raises_exception(self, calculator, sample_position):
        """Test that negative or zero current price raises exception."""
        with pytest.raises(InvalidPriceError, match="Current price must be positive"):
            calculator.calculate_unrealized(sample_position, Decimal("-10.00"))

        with pytest.raises(InvalidPriceError, match="Current price must be positive"):
            calculator.calculate_unrealized(sample_position, Decimal("0.00"))

    def test_invalid_sale_price_raises_exception(self, calculator, sample_position):
        """Test that negative or zero sale price raises exception."""
        with pytest.raises(InvalidPriceError, match="Sale price must be positive"):
            calculator.calculate_realized(
                sample_position, sample_position, Decimal("-10.00")
            )

        with pytest.raises(InvalidPriceError, match="Sale price must be positive"):
            calculator.calculate_realized(
                sample_position, sample_position, Decimal("0.00")
            )

    def test_zero_avg_price_handled_gracefully(self, calculator):
        """Test handling of position with zero average price."""
        position = PositionResponse(
            id="00000000-0000-0000-0000-000000000001",
            ticker="TEST",
            market="US",
            entries=[],
            avg_price=Decimal("0.0000"),
            status="open",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        current_price = Decimal("100.00")

        result = calculator.calculate_unrealized(position, current_price)

        # With zero cost basis, any current value is 100% gain
        assert result.unrealized_pnl == Decimal("0.0000")
        assert result.unrealized_pnl_percent == Decimal("0.0000")
        assert result.realized_pnl == Decimal("0.0000")
        assert result.total_pnl == Decimal("0.0000")

    def test_empty_entries_handled_gracefully(self, calculator):
        """Test handling of position with empty entries list."""
        position = PositionResponse(
            id="00000000-0000-0000-0000-000000000001",
            ticker="TEST",
            market="US",
            entries=[],
            avg_price=Decimal("0.0000"),
            status="open",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        current_price = Decimal("120.00")

        result = calculator.calculate_unrealized(position, current_price)

        assert result.unrealized_pnl == Decimal("0.0000")
        assert result.unrealized_pnl_percent == Decimal("0.0000")
        assert result.realized_pnl == Decimal("0.0000")
        assert result.total_pnl == Decimal("0.0000")
