"""
TP/SL Judgment Engine.
Pure calculation engine for Take Profit / Stop Loss decisions.
"""

from decimal import ROUND_HALF_UP, Decimal

from app.domain.ai.schemas import StopLossLevel, TakeProfitLevel
from app.domain.position.pnl_calculator import PnLCalculator
from app.domain.position.schemas import TpSlDecision


class TpSlEngine:
    """
    Pure TP/SL judgment engine.
    No I/O, no async, no AI, no side effects.
    Evaluates current price against TP/SL level lists.
    """

    def __init__(self):
        self._pnl_calculator = PnLCalculator()

    def evaluate(
        self,
        avg_price: Decimal,
        current_price: Decimal,
        total_quantity: Decimal,
        take_profit_levels: list[TakeProfitLevel],
        stop_loss_levels: list[StopLossLevel],
    ) -> TpSlDecision:
        """
        Evaluate TP/SL for a position.
        SL takes priority over TP if both triggered.
        """
        if total_quantity == 0:
            return self._hold_decision(Decimal("0"))

        # Calculate current PnL%
        current_pnl_pct = self._calculate_pnl_percent(avg_price, current_price)

        # Check SL first (priority)
        sl_decision = self._check_sl(
            current_pnl_pct,
            total_quantity,
            avg_price,
            current_price,
            stop_loss_levels
        )
        if sl_decision:
            return sl_decision

        # Check TP
        tp_decision = self._check_tp(
            current_pnl_pct,
            total_quantity,
            avg_price,
            current_price,
            take_profit_levels
        )
        if tp_decision:
            return tp_decision

        return self._hold_decision(current_pnl_pct)

    def _calculate_pnl_percent(
        self, avg_price: Decimal, current_price: Decimal
    ) -> Decimal:
        """Calculate P&L percentage: (current_price - avg_price) / avg_price * 100"""
        if avg_price == 0:
            return Decimal("0")

        pnl_pct = ((current_price - avg_price) / avg_price * 100)
        return pnl_pct.quantize(Decimal("0.0001"), ROUND_HALF_UP)

    def _calculate_realized_pnl(
        self, avg_price: Decimal, current_price: Decimal, sell_quantity: Decimal
    ) -> Decimal:
        """
        Calculate realized PnL estimate.
        Formula: (current_price - avg_price) * sell_quantity
        """
        realized = (current_price - avg_price) * sell_quantity
        return realized.quantize(Decimal("0.0001"), ROUND_HALF_UP)

    def _check_tp(
        self,
        current_pnl_pct: Decimal,
        total_quantity: Decimal,
        avg_price: Decimal,
        current_price: Decimal,
        levels: list[TakeProfitLevel]
    ) -> TpSlDecision | None:
        """
        Find highest triggered TP level.
        Levels sorted ascending; take last triggered.
        """
        if not levels:
            return None

        sorted_levels = sorted(levels, key=lambda x: Decimal(str(x.pct)))
        triggered = [
            lvl for lvl in sorted_levels
            if current_pnl_pct >= Decimal(str(lvl.pct))
        ]
        if not triggered:
            return None

        highest = triggered[-1]
        sell_ratio = Decimal(str(highest.sell_ratio))
        sell_quantity = (total_quantity * sell_ratio).quantize(
            Decimal("0.0001"), ROUND_HALF_UP
        )
        action = "full_exit" if sell_ratio >= Decimal("1.0") else "partial_sell"
        realized = self._calculate_realized_pnl(avg_price, current_price, sell_quantity)

        return TpSlDecision(
            action=action,
            triggered_by="tp",
            triggered_level_pct=Decimal(str(highest.pct)).quantize(Decimal("0.0001")),
            sell_quantity=sell_quantity,
            sell_ratio=sell_ratio.quantize(Decimal("0.0001")),
            current_pnl_pct=current_pnl_pct,
            realized_pnl_estimate=realized,
        )

    def _check_sl(
        self,
        current_pnl_pct: Decimal,
        total_quantity: Decimal,
        avg_price: Decimal,
        current_price: Decimal,
        levels: list[StopLossLevel]
    ) -> TpSlDecision | None:
        """
        Find most severe triggered SL level.
        Levels sorted ascending (most negative = most severe).
        """
        if not levels:
            return None

        sorted_levels = sorted(levels, key=lambda x: Decimal(str(x.pct)))
        triggered = [
            lvl for lvl in sorted_levels
            if current_pnl_pct <= Decimal(str(lvl.pct))
        ]
        if not triggered:
            return None

        most_severe = triggered[0]  # most negative pct
        sell_ratio = Decimal(str(most_severe.sell_ratio))
        sell_quantity = (total_quantity * sell_ratio).quantize(
            Decimal("0.0001"), ROUND_HALF_UP
        )
        action = "full_exit" if sell_ratio >= Decimal("1.0") else "partial_sell"
        realized = self._calculate_realized_pnl(avg_price, current_price, sell_quantity)

        return TpSlDecision(
            action=action,
            triggered_by="sl",
            triggered_level_pct=Decimal(str(most_severe.pct)).quantize(Decimal("0.0001")),
            sell_quantity=sell_quantity,
            sell_ratio=sell_ratio.quantize(Decimal("0.0001")),
            current_pnl_pct=current_pnl_pct,
            realized_pnl_estimate=realized,
        )

    def _hold_decision(self, current_pnl_pct: Decimal) -> TpSlDecision:
        """Return a hold decision with zero values."""
        return TpSlDecision(
            action="hold",
            triggered_by="none",
            triggered_level_pct=None,
            sell_quantity=Decimal("0.0000"),
            sell_ratio=Decimal("0.0000"),
            current_pnl_pct=current_pnl_pct,
            realized_pnl_estimate=Decimal("0.0000"),
        )
