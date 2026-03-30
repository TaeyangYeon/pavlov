"""
Change detector for strategy comparison.
Detects meaningful strategy changes to prevent notification spam.
"""

from decimal import Decimal

from app.domain.strategy.schemas import UnifiedStrategy


class ChangeDetector:
    """
    Detects meaningful strategy changes vs last stored strategy.
    Single responsibility: comparison logic only.
    Prevents notification spam when strategy is unchanged.
    """

    QUANTITY_PRECISION = Decimal("0.01")

    def has_changed(
        self,
        current: UnifiedStrategy,
        last: dict | None,
    ) -> bool:
        """
        Returns True if strategy meaningfully changed.
        Compares: ticker, final_action, sell_quantity (2dp).

        Args:
            current: Current strategy to check
            last: Last stored strategy as dict, or None

        Returns:
            True if strategy changed, False otherwise
        """
        if last is None:
            return True

        if current.ticker != last.get("ticker"):
            return True

        if current.final_action != last.get("action"):
            return True

        # Compare sell quantities with 2-decimal precision
        current_qty = current.sell_quantity.quantize(
            self.QUANTITY_PRECISION
        )
        last_qty = Decimal(
            str(last.get("sell_quantity", "0"))
        ).quantize(self.QUANTITY_PRECISION)

        return current_qty != last_qty

