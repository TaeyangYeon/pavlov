"""Repository for analysis_log table operations."""
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.models.analysis_log import AnalysisLog


class AnalysisLogRepository:
    """
    Repository for analysis_log table.
    Critical for Step 17 Missed Execution Recovery.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(
        self,
        date: date,
        market: str,
        executed: bool,
        ai_response: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> AnalysisLog:
        """Insert new analysis log entry."""
        log = AnalysisLog(
            date=date,
            market=market,
            executed=executed,
            ai_response=ai_response,
            error_message=error_message,
        )
        self._session.add(log)
        await self._session.commit()
        await self._session.refresh(log)
        return log

    async def mark_executed(self, log_id: UUID) -> None:
        """Mark analysis log as successfully executed."""
        stmt = (
            update(AnalysisLog)
            .where(AnalysisLog.id == log_id)
            .values(executed=True)
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def get_unexecuted(self, market: str, target_date: date) -> list[AnalysisLog]:
        """
        Fetch unexecuted logs for given market and date.
        CRITICAL: used by Step 17 Missed Execution Recovery.
        """
        stmt = select(AnalysisLog).where(
            AnalysisLog.market == market,
            AnalysisLog.date == target_date,
            AnalysisLog.executed == False,  # noqa: E712
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def exists(self, market: str, target_date: date) -> bool:
        """
        Check if analysis was already executed today.
        Prevents duplicate runs.
        """
        stmt = select(AnalysisLog).where(
            AnalysisLog.market == market,
            AnalysisLog.date == target_date,
            AnalysisLog.executed == True,  # noqa: E712
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
