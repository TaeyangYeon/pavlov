"""
MarketDataRepository implementation.
Repository for market_data table with SQLAlchemy 2.0 async operations.
Single responsibility: DB read/write for OHLCV data only.
"""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.models.market_data import MarketData


class MarketDataRepository:
    """
    Repository for market_data table.
    Single responsibility: DB read/write for OHLCV data.
    No business logic, no caching logic.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_date(
        self, ticker: str, market: str, target_date: date
    ) -> dict | None:
        """
        Fetch single OHLCV record from DB.
        Returns None if not found.
        """
        stmt = select(MarketData).where(
            MarketData.ticker == ticker,
            MarketData.market == market,
            MarketData.date == target_date,
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_dict(row)

    async def get_multiple_by_date(
        self, tickers: list[str], market: str, target_date: date
    ) -> list[dict]:
        """Fetch multiple tickers for same date."""
        stmt = select(MarketData).where(
            MarketData.ticker.in_(tickers),
            MarketData.market == market,
            MarketData.date == target_date,
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_dict(row) for row in rows]

    async def bulk_upsert(self, data_list: list[dict]) -> None:
        """
        Insert or update market data records.
        Uses PostgreSQL ON CONFLICT DO UPDATE (upsert).
        Skips silently if data_list is empty.
        """
        if not data_list:
            return

        stmt = pg_insert(MarketData).values(data_list)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_market_data_ticker_market_date",
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "volume": stmt.excluded.volume,
                "updated_at": func.now(),
            },
        )
        await self._session.execute(stmt)
        await self._session.commit()

    def _to_dict(self, row: MarketData) -> dict:
        """Convert ORM model to standard OHLCV dict."""
        return {
            "ticker": row.ticker,
            "market": str(row.market.value),
            "date": row.date.isoformat(),
            "open": float(row.open),
            "high": float(row.high),
            "low": float(row.low),
            "close": float(row.close),
            "volume": int(row.volume),
        }
