"""
Repository for StrategyOutput database operations.
SQLAlchemy 2.0 async implementation.
"""

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.strategy.schemas import UnifiedStrategy
from app.infra.db.models.analysis_log import AnalysisLog
from app.infra.db.models.strategy_output import StrategyOutput


class StrategyOutputRepository:
    """Repository for strategy output database operations."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(
        self,
        analysis_log_id: UUID,
        strategy: UnifiedStrategy,
    ) -> StrategyOutput:
        """
        Save unified strategy to DB.
        
        Args:
            analysis_log_id: Analysis log foreign key
            strategy: Unified strategy to save
            
        Returns:
            Saved StrategyOutput model
        """
        # Extract TP/SL levels from strategy if available
        take_profit_levels = []
        stop_loss_levels = []
        
        if strategy.tp_sl_result:
            # Note: TP/SL levels are in the original AI strategy,
            # not in the evaluation response
            pass
        
        if strategy.ai_strategy:
            take_profit_levels = [
                {"pct": float(level.pct), "sell_ratio": float(level.sell_ratio)}
                for level in strategy.ai_strategy.take_profit
            ]
            stop_loss_levels = [
                {"pct": float(level.pct), "sell_ratio": float(level.sell_ratio)}
                for level in strategy.ai_strategy.stop_loss
            ]

        row = StrategyOutput(
            analysis_log_id=analysis_log_id,
            ticker=strategy.ticker,
            action=strategy.final_action,
            take_profit_levels=take_profit_levels,
            stop_loss_levels=stop_loss_levels,
            rationale=strategy.rationale[:100],  # Truncate to model limit
            confidence=strategy.confidence,
        )
        
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return row

    async def get_latest(
        self,
        ticker: str,
        market: str,
        target_date: date,
    ) -> dict | None:
        """
        Fetch most recent strategy for ticker on date.
        
        Args:
            ticker: Stock ticker symbol
            market: Market (KR/US)
            target_date: Date to search for
            
        Returns:
            Strategy dict or None if not found
        """
        stmt = (
            select(StrategyOutput)
            .join(
                AnalysisLog,
                StrategyOutput.analysis_log_id == AnalysisLog.id
            )
            .where(
                StrategyOutput.ticker == ticker,
                AnalysisLog.market == market,
                AnalysisLog.date == target_date,
            )
            .order_by(StrategyOutput.created_at.desc())
            .limit(1)
        )
        
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        
        if row is None:
            return None
            
        return {
            "ticker": row.ticker,
            "action": row.action.value,  # Enum to string
            "sell_quantity": str(row.confidence),  # Note: using confidence as proxy
            "rationale": row.rationale,
        }

    async def get_by_analysis_log(
        self,
        analysis_log_id: UUID,
    ) -> list[StrategyOutput]:
        """
        Fetch all strategies for an analysis log.
        
        Args:
            analysis_log_id: Analysis log ID
            
        Returns:
            List of StrategyOutput models
        """
        stmt = select(StrategyOutput).where(
            StrategyOutput.analysis_log_id == analysis_log_id
        )
        
        result = await self._session.execute(stmt)
        return list(result.scalars().all())