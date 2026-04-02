"""
Unit tests for VirtualPortfolio.
Tests portfolio state management with exact decimal calculations.
"""

from datetime import date
from decimal import Decimal

import pytest
from app.domain.backtest.exceptions import (
    InsufficientCapitalError,
    InsufficientPositionError,
)
from app.domain.backtest.portfolio import VirtualPortfolio


@pytest.fixture
def portfolio():
    """VirtualPortfolio instance with 10M initial capital."""
    return VirtualPortfolio(Decimal("10000000"))


class TestVirtualPortfolio:
    """Test cases for virtual portfolio management."""

    def test_portfolio_initial_state(self, portfolio):
        """Test portfolio initial state is correct."""
        assert portfolio.cash == Decimal("10000000")
        assert portfolio.positions == {}
        assert portfolio.realized_pnl == Decimal("0")
        assert len(portfolio.trades) == 0

    def test_portfolio_buy_reduces_cash(self, portfolio):
        """Test buying stock reduces cash and creates position."""
        portfolio.buy(
            ticker="AAPL",
            quantity=Decimal("10"),
            price=Decimal("150000"),
            trade_date=date(2024, 1, 1),
        )

        # Cash should be reduced by 10 * 150,000 = 1,500,000
        expected_cash = Decimal("10000000") - Decimal("1500000")
        assert portfolio.cash == expected_cash

        # Position should be created
        positions = portfolio.positions
        assert "AAPL" in positions
        assert positions["AAPL"]["quantity"] == Decimal("10")
        assert positions["AAPL"]["avg_price"] == Decimal("150000.0000")
        assert positions["AAPL"]["cost_basis"] == Decimal("1500000.0000")

    def test_portfolio_buy_insufficient_cash_raises(self, portfolio):
        """Test buying with insufficient cash raises exception."""
        # Try to buy more than we can afford
        with pytest.raises(InsufficientCapitalError) as exc_info:
            portfolio.buy(
                ticker="AAPL",
                quantity=Decimal("1000"),
                price=Decimal("150000"),
                trade_date=date(2024, 1, 1),
            )

        error = exc_info.value
        assert "Insufficient capital" in str(error)
        assert error.code == "INSUFFICIENT_CAPITAL"

        # Cash should be unchanged
        assert portfolio.cash == Decimal("10000000")
        assert portfolio.positions == {}

    def test_portfolio_sell_increases_cash(self, portfolio):
        """Test selling stock increases cash and calculates P&L."""
        # First buy
        portfolio.buy(
            ticker="AAPL",
            quantity=Decimal("10"),
            price=Decimal("150000"),
            trade_date=date(2024, 1, 1),
        )

        initial_cash = portfolio.cash

        # Then sell part at higher price
        trade = portfolio.sell(
            ticker="AAPL",
            quantity=Decimal("5"),
            price=Decimal("165000"),
            trade_date=date(2024, 1, 5),
            holding_days=4,
        )

        # Cash should increase by 5 * 165,000 = 825,000
        expected_cash = initial_cash + Decimal("825000")
        assert portfolio.cash == expected_cash

        # P&L should be (165,000 - 150,000) * 5 = 75,000
        assert trade.pnl == Decimal("75000.0000")
        assert portfolio.realized_pnl == Decimal("75000.0000")

        # Position should be reduced
        positions = portfolio.positions
        assert positions["AAPL"]["quantity"] == Decimal("5")

    def test_portfolio_sell_more_than_held_raises(self, portfolio):
        """Test selling more than held raises exception."""
        # Buy 5 shares
        portfolio.buy(
            ticker="AAPL",
            quantity=Decimal("5"),
            price=Decimal("150000"),
            trade_date=date(2024, 1, 1),
        )

        # Try to sell 10 shares
        with pytest.raises(InsufficientPositionError) as exc_info:
            portfolio.sell(
                ticker="AAPL",
                quantity=Decimal("10"),
                price=Decimal("165000"),
                trade_date=date(2024, 1, 5),
            )

        error = exc_info.value
        assert "Insufficient AAPL" in str(error)
        assert error.code == "INSUFFICIENT_POSITION"

    def test_portfolio_full_sell_removes_position(self, portfolio):
        """Test selling all shares removes position."""
        # Buy and then sell all
        portfolio.buy(
            ticker="AAPL",
            quantity=Decimal("10"),
            price=Decimal("150000"),
            trade_date=date(2024, 1, 1),
        )

        portfolio.sell(
            ticker="AAPL",
            quantity=Decimal("10"),
            price=Decimal("165000"),
            trade_date=date(2024, 1, 5),
        )

        # Position should be removed
        assert "AAPL" not in portfolio.positions

        # P&L should be calculated
        assert portfolio.realized_pnl == Decimal("150000.0000")  # 15,000 * 10

    def test_portfolio_avg_price_updates_on_additional_buy(self, portfolio):
        """Test average price calculation on additional purchases."""
        # First buy: 10 shares @ 100
        portfolio.buy(
            ticker="AAPL",
            quantity=Decimal("10"),
            price=Decimal("100000"),
            trade_date=date(2024, 1, 1),
        )

        # Second buy: 10 shares @ 120
        portfolio.buy(
            ticker="AAPL",
            quantity=Decimal("10"),
            price=Decimal("120000"),
            trade_date=date(2024, 1, 2),
        )

        # Average should be (10*100 + 10*120) / 20 = 110
        positions = portfolio.positions
        assert positions["AAPL"]["quantity"] == Decimal("20")
        assert positions["AAPL"]["avg_price"] == Decimal("110000.0000")
        assert positions["AAPL"]["cost_basis"] == Decimal("2200000.0000")

    def test_portfolio_total_value_calculation(self, portfolio):
        """Test total portfolio value calculation."""
        # Buy position
        portfolio.buy(
            ticker="AAPL",
            quantity=Decimal("10"),
            price=Decimal("150000"),
            trade_date=date(2024, 1, 1),
        )

        # Calculate total value with current price
        current_prices = {"AAPL": Decimal("150000")}
        total_value = portfolio.total_value(current_prices)

        # Should equal remaining cash + position value
        expected_cash = Decimal("10000000") - Decimal("1500000")
        expected_position_value = Decimal("10") * Decimal("150000")
        expected_total = expected_cash + expected_position_value

        assert total_value == expected_total

    def test_portfolio_realized_pnl_on_sell(self, portfolio):
        """Test realized P&L calculation on sell."""
        # Buy 10 @ 100, sell 10 @ 130
        portfolio.buy(
            ticker="AAPL",
            quantity=Decimal("10"),
            price=Decimal("100000"),
            trade_date=date(2024, 1, 1),
        )

        trade = portfolio.sell(
            ticker="AAPL",
            quantity=Decimal("10"),
            price=Decimal("130000"),
            trade_date=date(2024, 1, 10),
        )

        # P&L should be (130,000 - 100,000) * 10 = 300,000
        assert trade.pnl == Decimal("300000.0000")
        assert portfolio.realized_pnl == Decimal("300000.0000")

    def test_portfolio_sell_ticker_not_held_raises(self, portfolio):
        """Test selling ticker not in portfolio raises exception."""
        with pytest.raises(InsufficientPositionError) as exc_info:
            portfolio.sell(
                ticker="MSFT",
                quantity=Decimal("10"),
                price=Decimal("100000"),
                trade_date=date(2024, 1, 1),
            )

        error = exc_info.value
        assert "Insufficient MSFT" in str(error)
        assert error.code == "INSUFFICIENT_POSITION"