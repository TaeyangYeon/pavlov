"""
Trailing Stop Engine.
Pure calculation engine with Decimal precision.
Implements ratchet mechanism: HWM only moves up.
Supports percentage and ATR-based trailing stops.
No I/O, no async, no side effects.
"""

from decimal import Decimal, ROUND_HALF_UP

from app.domain.position.schemas import TrailingStopConfig, TrailingStopResult

PRECISION = Decimal("0.0001")


class TrailingStopEngine:
    """
    Pure trailing stop calculation engine.
    Implements ratchet mechanism: HWM only moves up.
    Supports percentage and ATR-based trailing stops.
    No I/O, no async, no side effects.
    """

    def evaluate(
        self,
        current_price: Decimal,
        high_water_mark: Decimal | None,
        avg_price: Decimal,
        config: TrailingStopConfig,
    ) -> TrailingStopResult:
        """
        Evaluate trailing stop for current price.
        Updates high_water_mark (ratchet: only up).
        Returns TrailingStopResult with new HWM.
        """
        # Step 1: Initialize HWM if None
        effective_hwm = high_water_mark
        if effective_hwm is None:
            effective_hwm = max(avg_price, current_price)

        # Step 2: Ratchet — HWM only moves up
        new_hwm = max(
            effective_hwm, current_price
        ).quantize(PRECISION, ROUND_HALF_UP)

        # Step 3: Calculate stop price
        stop_price = self._calculate_stop_price(
            new_hwm, config
        )

        # Step 4: Evaluate trigger
        triggered = current_price <= stop_price

        # Step 5: Calculate trail distance %
        trail_distance_pct = self._calculate_trail_pct(
            new_hwm, stop_price
        )

        # Step 6: Calculate distance to stop %
        if current_price > 0:
            distance_to_stop_pct = (
                (current_price - stop_price)
                / current_price * Decimal("100")
            ).quantize(PRECISION, ROUND_HALF_UP)
        else:
            distance_to_stop_pct = Decimal("0.0000")

        return TrailingStopResult(
            triggered=triggered,
            action="full_exit" if triggered else "hold",
            high_water_mark=new_hwm,
            stop_price=stop_price,
            current_price=current_price,
            trail_distance_pct=trail_distance_pct,
            distance_to_stop_pct=distance_to_stop_pct,
        )

    def _calculate_stop_price(
        self,
        hwm: Decimal,
        config: TrailingStopConfig
    ) -> Decimal:
        """Calculate stop price based on configuration mode."""
        if config.mode == "percentage":
            return (
                hwm * (
                    Decimal("1")
                    - config.trail_pct / Decimal("100")
                )
            ).quantize(PRECISION, ROUND_HALF_UP)
        else:  # atr mode
            return (
                hwm - (config.atr_multiplier * config.atr_value)
            ).quantize(PRECISION, ROUND_HALF_UP)

    def _calculate_trail_pct(
        self,
        hwm: Decimal,
        stop_price: Decimal
    ) -> Decimal:
        """Calculate trail distance as percentage."""
        if hwm == 0:
            return Decimal("0.0000")
        return (
            (hwm - stop_price) / hwm * Decimal("100")
        ).quantize(PRECISION, ROUND_HALF_UP)