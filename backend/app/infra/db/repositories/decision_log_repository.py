"""
Decision log repository for behavioral analysis system.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.models.decision_log import DecisionLog


class DecisionLogRepository:
    """Repository for decision log operations."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def record(
        self,
        user_id: UUID,
        ticker: str,
        action: str,
        price: Decimal,
        quantity: Decimal,
        ai_suggested: bool,
        notes: str | None = None,
    ) -> DecisionLog:
        """Record a new decision log entry."""
        row = DecisionLog(
            user_id=user_id,
            ticker=ticker,
            action=action,
            price=price,
            quantity=quantity,
            ai_suggested=ai_suggested,
            notes=notes,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return row

    async def get_by_user(
        self,
        user_id: UUID,
        limit: int = 100,
        days: int = 30,
    ) -> list[DecisionLog]:
        """Get user decisions within time period."""
        cutoff = datetime.now() - timedelta(days=days)
        stmt = (
            select(DecisionLog)
            .where(
                DecisionLog.user_id == user_id,
                DecisionLog.created_at >= cutoff,
            )
            .order_by(DecisionLog.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_ticker(
        self,
        user_id: UUID,
        ticker: str,
        limit: int = 20,
    ) -> list[DecisionLog]:
        """Get user decisions for specific ticker."""
        stmt = (
            select(DecisionLog)
            .where(
                DecisionLog.user_id == user_id,
                DecisionLog.ticker == ticker,
            )
            .order_by(DecisionLog.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent(
        self,
        user_id: UUID,
        n: int = 10,
    ) -> list[DecisionLog]:
        """Get most recent N decisions for user."""
        stmt = (
            select(DecisionLog)
            .where(DecisionLog.user_id == user_id)
            .order_by(DecisionLog.created_at.desc())
            .limit(n)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_ticker_in_period(
        self,
        user_id: UUID,
        ticker: str,
        days: int = 7,
    ) -> int:
        """Count trades for ticker in time period."""
        cutoff = datetime.now() - timedelta(days=days)
        stmt = (
            select(func.count(DecisionLog.id))
            .where(
                DecisionLog.user_id == user_id,
                DecisionLog.ticker == ticker,
                DecisionLog.created_at >= cutoff,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0