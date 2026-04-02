"""
BacktestRepository implementation.
Repository for backtest_results table with SQLAlchemy 2.0 async operations.
Single responsibility: DB read/write for backtest results only.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.backtest.schemas import BacktestRunResult
from app.infra.db.models.backtest_result import BacktestResult


class BacktestRepository:
    """
    Repository for backtest_results table.
    Single responsibility: DB read/write for backtest results.
    No business logic, no caching logic.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(
        self,
        result: BacktestRunResult,
        parameters: dict,
    ) -> BacktestResult:
        """
        Save backtest result to database.
        Returns the saved DB record.
        """
        row = BacktestResult(
            ticker=result.ticker,
            market=result.market,
            start_date=result.start_date,
            end_date=result.end_date,
            initial_capital=result.initial_capital,
            final_capital=result.final_capital,
            total_return_pct=result.metrics.total_return_pct,
            max_drawdown_pct=result.metrics.max_drawdown_pct,
            win_rate=result.metrics.win_rate,
            sharpe_ratio=result.metrics.sharpe_ratio,
            total_trades=result.metrics.total_trades,
            parameters_json=parameters,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return row

    async def get_by_ticker(
        self,
        ticker: str,
        limit: int = 10,
    ) -> list[BacktestResult]:
        """
        Fetch backtest results for a ticker, newest first.
        Limited to prevent excessive data transfer.
        """
        stmt = (
            select(BacktestResult)
            .where(BacktestResult.ticker == ticker)
            .order_by(BacktestResult.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest(
        self, ticker: str, market: str
    ) -> BacktestResult | None:
        """
        Fetch the most recent backtest result for ticker/market.
        Returns None if not found.
        """
        stmt = (
            select(BacktestResult)
            .where(
                BacktestResult.ticker == ticker,
                BacktestResult.market == market,
            )
            .order_by(BacktestResult.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, backtest_id: str) -> BacktestResult | None:
        """
        Fetch backtest result by ID.
        Returns None if not found.
        """
        stmt = select(BacktestResult).where(BacktestResult.id == backtest_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_old_results(self, ticker: str, keep_count: int = 20) -> int:
        """
        Delete old backtest results for a ticker, keeping only the most recent.
        Returns number of deleted records.
        """
        # Get IDs of records to keep
        keep_stmt = (
            select(BacktestResult.id)
            .where(BacktestResult.ticker == ticker)
            .order_by(BacktestResult.created_at.desc())
            .limit(keep_count)
        )
        keep_result = await self._session.execute(keep_stmt)
        keep_ids = [row[0] for row in keep_result.fetchall()]

        if not keep_ids:
            return 0

        # Delete records not in keep list
        delete_stmt = select(BacktestResult).where(
            BacktestResult.ticker == ticker,
            BacktestResult.id.notin_(keep_ids),
        )
        delete_result = await self._session.execute(delete_stmt)
        old_records = list(delete_result.scalars().all())

        for record in old_records:
            await self._session.delete(record)

        await self._session.commit()
        return len(old_records)