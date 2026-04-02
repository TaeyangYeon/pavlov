"""
Unit tests for PerformanceMetrics.
Tests performance calculation with known expected values.
"""

from datetime import date
from decimal import Decimal

import pytest
from app.domain.backtest.metrics import PerformanceMetrics
from app.domain.backtest.schemas import BacktestTrade, DailyValue


@pytest.fixture
def metrics_calculator():
    """PerformanceMetrics instance for testing."""
    return PerformanceMetrics()


@pytest.fixture
def known_daily_values():
    """Known daily values for predictable test results."""
    return [
        DailyValue(
            date=date(2024, 1, 1),
            portfolio_value=Decimal("10000"),
            cash=Decimal("5000"),
            position_value=Decimal("5000"),
            daily_return_pct=Decimal("0.0000"),
        ),
        DailyValue(
            date=date(2024, 1, 2),
            portfolio_value=Decimal("10100"),
            cash=Decimal("5000"),
            position_value=Decimal("5100"),
            daily_return_pct=Decimal("1.0000"),
        ),
        DailyValue(
            date=date(2024, 1, 3),
            portfolio_value=Decimal("10050"),
            cash=Decimal("5000"),
            position_value=Decimal("5050"),
            daily_return_pct=Decimal("-0.4950"),
        ),
        DailyValue(
            date=date(2024, 1, 4),
            portfolio_value=Decimal("10200"),
            cash=Decimal("5000"),
            position_value=Decimal("5200"),
            daily_return_pct=Decimal("1.4925"),
        ),
        DailyValue(
            date=date(2024, 1, 5),
            portfolio_value=Decimal("9900"),
            cash=Decimal("5000"),
            position_value=Decimal("4900"),
            daily_return_pct=Decimal("-2.9412"),
        ),
        DailyValue(
            date=date(2024, 1, 6),
            portfolio_value=Decimal("10300"),
            cash=Decimal("5000"),
            position_value=Decimal("5300"),
            daily_return_pct=Decimal("4.0404"),
        ),
        DailyValue(
            date=date(2024, 1, 7),
            portfolio_value=Decimal("10250"),
            cash=Decimal("5000"),
            position_value=Decimal("5250"),
            daily_return_pct=Decimal("-0.4854"),
        ),
        DailyValue(
            date=date(2024, 1, 8),
            portfolio_value=Decimal("10500"),
            cash=Decimal("5000"),
            position_value=Decimal("5500"),
            daily_return_pct=Decimal("2.4390"),
        ),
        DailyValue(
            date=date(2024, 1, 9),
            portfolio_value=Decimal("10400"),
            cash=Decimal("5000"),
            position_value=Decimal("5400"),
            daily_return_pct=Decimal("-0.9524"),
        ),
        DailyValue(
            date=date(2024, 1, 10),
            portfolio_value=Decimal("10600"),
            cash=Decimal("5000"),
            position_value=Decimal("5600"),
            daily_return_pct=Decimal("1.9231"),
        ),
    ]


@pytest.fixture
def known_trades():
    """Known trades with predictable P&L."""
    return [
        BacktestTrade(
            date=date(2024, 1, 1),
            ticker="TEST",
            action="buy",
            quantity=Decimal("10"),
            price=Decimal("100"),
            pnl=Decimal("0"),
            trigger="signal",
            holding_days=0,
        ),
        BacktestTrade(
            date=date(2024, 1, 3),
            ticker="TEST",
            action="sell",
            quantity=Decimal("5"),
            price=Decimal("110"),
            pnl=Decimal("50"),  # (110-100) * 5
            trigger="tp",
            holding_days=2,
        ),
        BacktestTrade(
            date=date(2024, 1, 5),
            ticker="TEST",
            action="sell",
            quantity=Decimal("3"),
            price=Decimal("95"),
            pnl=Decimal("-15"),  # (95-100) * 3
            trigger="sl",
            holding_days=4,
        ),
        BacktestTrade(
            date=date(2024, 1, 7),
            ticker="TEST",
            action="buy",
            quantity=Decimal("8"),
            price=Decimal("105"),
            pnl=Decimal("0"),
            trigger="signal",
            holding_days=0,
        ),
        BacktestTrade(
            date=date(2024, 1, 9),
            ticker="TEST",
            action="sell",
            quantity=Decimal("8"),
            price=Decimal("115"),
            pnl=Decimal("80"),  # (115-105) * 8
            trigger="tp",
            holding_days=2,
        ),
        BacktestTrade(
            date=date(2024, 1, 10),
            ticker="TEST",
            action="sell",
            quantity=Decimal("2"),
            price=Decimal("90"),
            pnl=Decimal("-20"),  # (90-100) * 2
            trigger="eod",
            holding_days=9,
        ),
    ]


class TestPerformanceMetrics:
    """Test cases for performance metrics calculation."""

    def test_total_return_pct_known_value(
        self, metrics_calculator, known_daily_values, known_trades
    ):
        """Test total return calculation with known values."""
        initial_capital = Decimal("10000")
        metrics = metrics_calculator.calculate(
            initial_capital, known_daily_values, known_trades
        )

        # Final value: 10600, initial: 10000
        # Total return: (10600 - 10000) / 10000 * 100 = 6.0000%
        assert metrics.total_return_pct == Decimal("6.0000")

    def test_max_drawdown_calculation(
        self, metrics_calculator, known_daily_values, known_trades
    ):
        """Test maximum drawdown calculation."""
        initial_capital = Decimal("10000")
        metrics = metrics_calculator.calculate(
            initial_capital, known_daily_values, known_trades
        )

        # Peak at 10200 (day 4), then drops to 9900 (day 5)
        # Drawdown = (9900 - 10200) / 10200 * 100 = -2.9412%
        assert metrics.max_drawdown_pct == Decimal("-2.9412")

    def test_win_rate_known_value(
        self, metrics_calculator, known_daily_values, known_trades
    ):
        """Test win rate calculation with known trades."""
        initial_capital = Decimal("10000")
        metrics = metrics_calculator.calculate(
            initial_capital, known_daily_values, known_trades
        )

        # Sell trades: +50, -15, +80, -20
        # Winning: 2 out of 4 = 0.5000
        assert metrics.win_rate == Decimal("0.5000")
        assert metrics.total_trades == 4
        assert metrics.winning_trades == 2
        assert metrics.losing_trades == 2

    def test_best_day_pct_known_value(
        self, metrics_calculator, known_daily_values, known_trades
    ):
        """Test best day percentage calculation."""
        initial_capital = Decimal("10000")
        metrics = metrics_calculator.calculate(
            initial_capital, known_daily_values, known_trades
        )

        # Best day return: +4.0404% on day 6
        assert metrics.best_day_pct == Decimal("4.0404")

    def test_worst_day_pct_known_value(
        self, metrics_calculator, known_daily_values, known_trades
    ):
        """Test worst day percentage calculation."""
        initial_capital = Decimal("10000")
        metrics = metrics_calculator.calculate(
            initial_capital, known_daily_values, known_trades
        )

        # Worst day return: -2.9412% on day 5
        assert metrics.worst_day_pct == Decimal("-2.9412")

    def test_sharpe_ratio_positive_for_positive_returns(
        self, metrics_calculator, known_daily_values, known_trades
    ):
        """Test Sharpe ratio calculation for positive returns."""
        initial_capital = Decimal("10000")
        metrics = metrics_calculator.calculate(
            initial_capital, known_daily_values, known_trades
        )

        # With net positive returns, Sharpe should be positive
        assert metrics.sharpe_ratio is not None
        assert metrics.sharpe_ratio > Decimal("0")

    def test_sharpe_ratio_zero_std_returns_none(self, metrics_calculator):
        """Test Sharpe ratio returns None when standard deviation is zero."""
        # Create flat returns (no volatility)
        flat_values = [
            DailyValue(
                date=date(2024, 1, i),
                portfolio_value=Decimal("10000"),
                cash=Decimal("5000"),
                position_value=Decimal("5000"),
                daily_return_pct=Decimal("0.0000"),
            )
            for i in range(1, 11)
        ]

        metrics = metrics_calculator.calculate(
            Decimal("10000"), flat_values, []
        )

        # Zero standard deviation should result in None Sharpe ratio
        assert metrics.sharpe_ratio is None

    def test_avg_holding_days_calculation(
        self, metrics_calculator, known_daily_values, known_trades
    ):
        """Test average holding days calculation."""
        initial_capital = Decimal("10000")
        metrics = metrics_calculator.calculate(
            initial_capital, known_daily_values, known_trades
        )

        # Holding days: 2, 4, 2, 9 = average 4.25
        assert metrics.avg_holding_days == Decimal("4.2500")

    def test_metrics_all_fields_are_decimal(
        self, metrics_calculator, known_daily_values, known_trades
    ):
        """Test all metric fields are Decimal type."""
        initial_capital = Decimal("10000")
        metrics = metrics_calculator.calculate(
            initial_capital, known_daily_values, known_trades
        )

        assert isinstance(metrics.total_return_pct, Decimal)
        assert isinstance(metrics.max_drawdown_pct, Decimal)
        assert isinstance(metrics.win_rate, Decimal)
        assert isinstance(metrics.best_day_pct, Decimal)
        assert isinstance(metrics.worst_day_pct, Decimal)
        assert isinstance(metrics.avg_holding_days, Decimal)
        # sharpe_ratio can be None
        if metrics.sharpe_ratio is not None:
            assert isinstance(metrics.sharpe_ratio, Decimal)

    def test_empty_daily_values_returns_empty_metrics(self, metrics_calculator):
        """Test empty daily values returns zero metrics."""
        metrics = metrics_calculator.calculate(
            Decimal("10000"), [], []
        )

        assert metrics.total_return_pct == Decimal("0")
        assert metrics.max_drawdown_pct == Decimal("0")
        assert metrics.win_rate == Decimal("0")
        assert metrics.total_trades == 0
        assert metrics.sharpe_ratio is None

    def test_no_trades_win_rate_zero(self, metrics_calculator, known_daily_values):
        """Test win rate is zero when no trades exist."""
        metrics = metrics_calculator.calculate(
            Decimal("10000"), known_daily_values, []
        )

        assert metrics.win_rate == Decimal("0")
        assert metrics.total_trades == 0
        assert metrics.winning_trades == 0
        assert metrics.losing_trades == 0