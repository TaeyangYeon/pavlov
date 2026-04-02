"""
Pure performance metrics calculator.
Input: daily portfolio values + trade list
No I/O, deterministic.
"""

import math
from decimal import Decimal, ROUND_HALF_UP

from app.domain.backtest.schemas import BacktestMetrics, BacktestTrade, DailyValue

PRECISION = Decimal("0.0001")
TRADING_DAYS_PER_YEAR = 252


class PerformanceMetrics:
    """
    Pure performance metrics calculator.
    Input: daily portfolio values + trade list
    No I/O, deterministic.
    """

    def calculate(
        self,
        initial_capital: Decimal,
        daily_values: list[DailyValue],
        trades: list[BacktestTrade],
    ) -> BacktestMetrics:
        if not daily_values:
            return self._empty_metrics()

        final_value = daily_values[-1].portfolio_value

        # Total return
        total_return = (
            (final_value - initial_capital) / initial_capital * Decimal("100")
        ).quantize(PRECISION, ROUND_HALF_UP)

        # Daily returns
        daily_returns = self._calculate_daily_returns(daily_values)

        # Max drawdown
        max_dd = self._calculate_max_drawdown(
            [dv.portfolio_value for dv in daily_values]
        )

        # Trade statistics
        sell_trades = [t for t in trades if t.action == "sell"]
        winning = [t for t in sell_trades if t.pnl > 0]
        losing = [t for t in sell_trades if t.pnl <= 0]
        total_tr = len(sell_trades)
        win_rate = (
            Decimal(str(len(winning))) / Decimal(str(total_tr))
            if total_tr > 0
            else Decimal("0")
        ).quantize(PRECISION, ROUND_HALF_UP)

        # Sharpe ratio
        sharpe = self._calculate_sharpe(daily_returns)

        # Best/worst day
        best_day = max(daily_returns) if daily_returns else Decimal("0")
        worst_day = min(daily_returns) if daily_returns else Decimal("0")

        # Avg holding days
        holding_days_list = [
            t.holding_days for t in sell_trades if t.holding_days > 0
        ]
        avg_holding = (
            Decimal(str(sum(holding_days_list) / len(holding_days_list))).quantize(
                PRECISION
            )
            if holding_days_list
            else Decimal("0")
        )

        return BacktestMetrics(
            total_return_pct=total_return,
            max_drawdown_pct=max_dd,
            win_rate=win_rate,
            total_trades=total_tr,
            winning_trades=len(winning),
            losing_trades=len(losing),
            sharpe_ratio=sharpe,
            best_day_pct=best_day,
            worst_day_pct=worst_day,
            avg_holding_days=avg_holding,
        )

    def _calculate_daily_returns(self, daily_values: list[DailyValue]) -> list[Decimal]:
        returns = []
        for i in range(1, len(daily_values)):
            prev = daily_values[i - 1].portfolio_value
            curr = daily_values[i].portfolio_value
            if prev > 0:
                r = ((curr - prev) / prev * Decimal("100")).quantize(
                    PRECISION, ROUND_HALF_UP
                )
                returns.append(r)
        return returns

    def _calculate_max_drawdown(self, values: list[Decimal]) -> Decimal:
        if len(values) < 2:
            return Decimal("0")

        peak = values[0]
        max_dd = Decimal("0")

        for v in values[1:]:
            if v > peak:
                peak = v
            drawdown = ((v - peak) / peak * Decimal("100")).quantize(
                PRECISION, ROUND_HALF_UP
            )
            if drawdown < max_dd:
                max_dd = drawdown

        return max_dd

    def _calculate_sharpe(self, daily_returns: list[Decimal]) -> Decimal | None:
        if len(daily_returns) < 2:
            return None

        n = len(daily_returns)
        mean = sum(daily_returns) / Decimal(str(n))
        variance = sum((r - mean) ** 2 for r in daily_returns) / Decimal(str(n - 1))

        std = Decimal(str(math.sqrt(float(variance))))
        if std == 0:
            return None

        annualized = (
            mean / std * Decimal(str(math.sqrt(TRADING_DAYS_PER_YEAR)))
        ).quantize(PRECISION, ROUND_HALF_UP)

        return annualized

    def _empty_metrics(self) -> BacktestMetrics:
        zero = Decimal("0")
        return BacktestMetrics(
            total_return_pct=zero,
            max_drawdown_pct=zero,
            win_rate=zero,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            sharpe_ratio=None,
            best_day_pct=zero,
            worst_day_pct=zero,
            avg_holding_days=zero,
        )