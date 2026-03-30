"""
Missed Execution Recovery Manager.
Detects and recovers missed analysis executions on startup.
"""

from datetime import date, timedelta
from typing import Any

from app.core.config import get_settings
from app.infra.db.models.analysis_log import AnalysisLog
from app.infra.db.repositories.analysis_log_repository import AnalysisLogRepository


class RecoveryManager:
    """
    Detects and recovers missed analysis executions.
    Checks analysis_log for unexecuted rows on startup.

    Recovery rules:
    - Only recover within MAX_RECOVERY_DAYS
    - Most recent missed date only (per market)
    - Partial execution: skip AI if response cached
    - Markets fully isolated
    """

    def __init__(
        self,
        kr_log_repo: AnalysisLogRepository,
        us_log_repo: AnalysisLogRepository,
    ):
        self._kr_repo = kr_log_repo
        self._us_repo = us_log_repo
        self._settings = get_settings()

    async def check_and_recover(self) -> dict[str, dict[str, Any]]:
        """
        Main entry point: check both markets and recover.
        Returns summary of recovery actions taken.
        """
        today = date.today()
        results = {
            "kr": await self._recover_market("KR", today, self._kr_repo),
            "us": await self._recover_market("US", today, self._us_repo),
        }
        return results

    async def _recover_market(
        self,
        market: str,
        today: date,
        repo: AnalysisLogRepository,
    ) -> dict[str, Any]:
        """
        Check and recover a single market.
        Returns: {"recovered": bool, "date": date | None, "error": str | None}
        """
        try:
            # Check last N days for unexecuted logs
            missed_logs: list[AnalysisLog] = []
            cutoff_date = today - timedelta(days=self._settings.max_recovery_days)

            for days_ago in range(1, self._settings.max_recovery_days + 1):
                check_date = today - timedelta(days=days_ago)
                unexecuted = await repo.get_unexecuted(market, check_date)
                missed_logs.extend(unexecuted)

            if not missed_logs:
                print(f"[Recovery] {market}: no missed executions found")
                return {"recovered": False, "date": None, "error": None}

            # Sort by date descending — most recent first
            missed_logs.sort(key=lambda x: x.date, reverse=True)

            # Check staleness — skip if beyond cutoff
            most_recent = missed_logs[0]
            if most_recent.date < cutoff_date:
                print(
                    f"[Recovery] {market}: skipping stale execution from "
                    f"{most_recent.date} (older than "
                    f"{self._settings.max_recovery_days} days)"
                )
                return {
                    "recovered": False,
                    "date": most_recent.date,
                    "error": "stale"
                }

            # Skip older logs, only run most recent
            if len(missed_logs) > 1:
                print(
                    f"[Recovery] {market}: found {len(missed_logs)} missed executions, "
                    f"recovering most recent: {most_recent.date}"
                )

            print(f"[Recovery] {market}: found missed execution for {most_recent.date}")

            # Determine if AI response cached
            skip_ai = most_recent.ai_response is not None
            if skip_ai:
                print(
                    f"[Recovery] {market}: AI response cached, "
                    f"skipping AI call for {most_recent.date}"
                )

            # Run recovery
            await self._run_recovery_job(
                market=market,
                target_date=most_recent.date,
                skip_ai=skip_ai,
            )

            print(f"[Recovery] {market}: recovery successful for {most_recent.date}")
            return {
                "recovered": True,
                "date": most_recent.date,
                "error": None
            }

        except Exception as e:
            print(f"[Recovery] {market}: recovery FAILED: {e}")
            return {
                "recovered": False,
                "date": None,
                "error": str(e)
            }

    async def _run_recovery_job(
        self,
        market: str,
        target_date: date,
        skip_ai: bool,
    ) -> None:
        """Dispatch to appropriate job function."""
        # Import here to avoid circular import issues
        from app.scheduler.jobs.kr_analysis_job import run_kr_analysis
        from app.scheduler.jobs.us_analysis_job import run_us_analysis

        if market == "KR":
            await run_kr_analysis(
                date_override=target_date,
                skip_ai_if_cached=skip_ai,
            )
        elif market == "US":
            await run_us_analysis(
                date_override=target_date,
                skip_ai_if_cached=skip_ai,
            )
        else:
            raise ValueError(f"Unknown market: {market}")
