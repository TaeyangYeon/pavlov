"""
Cooling-off period evaluation for emotional suppression system.
Pure calculation class with no I/O dependencies.
"""

from datetime import datetime
from app.domain.behavior.schemas import CoolingOffResult


class CoolingOffGate:
    """
    Pure cooling-off period evaluation.
    No I/O, no async, no side effects.
    Reuses notification check logic from Step 18.
    """

    def check(
        self,
        ticker: str,
        trade_time: datetime,
        last_alert_time: datetime | None,
        last_ai_recommendation: str | None,
        cooling_off_minutes: int,
    ) -> CoolingOffResult:
        """
        Check if trade is within cooling-off period.
        Boundary: elapsed >= cooling_off → NOT in period.
        """
        if last_alert_time is None:
            return CoolingOffResult(
                is_within_cooling_off=False,
                minutes_elapsed=0.0,
                minutes_remaining=0.0,
                cooling_off_minutes=cooling_off_minutes,
                last_alert_time=None,
                last_ai_recommendation=None,
                ticker=ticker,
            )

        elapsed = (trade_time - last_alert_time).total_seconds() / 60
        is_within = elapsed < cooling_off_minutes
        remaining = max(0.0, cooling_off_minutes - elapsed)

        return CoolingOffResult(
            is_within_cooling_off=is_within,
            minutes_elapsed=round(elapsed, 2),
            minutes_remaining=round(remaining, 2),
            cooling_off_minutes=cooling_off_minutes,
            last_alert_time=last_alert_time,
            last_ai_recommendation=last_ai_recommendation,
            ticker=ticker,
        )