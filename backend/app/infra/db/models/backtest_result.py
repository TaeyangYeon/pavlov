from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DECIMAL, Date, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as SQLAlchemyUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class BacktestResult(Base):
    """Backtest result model for storing backtest simulation results."""

    __tablename__ = "backtest_results"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Stock identification
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    market: Mapped[str] = mapped_column(String(5), nullable=False)

    # Backtest period
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Capital information
    initial_capital: Mapped[Decimal] = mapped_column(DECIMAL(15, 4), nullable=False)
    final_capital: Mapped[Decimal] = mapped_column(DECIMAL(15, 4), nullable=False)

    # Performance metrics
    total_return_pct: Mapped[Decimal] = mapped_column(DECIMAL(10, 4), nullable=False)
    max_drawdown_pct: Mapped[Decimal] = mapped_column(DECIMAL(10, 4), nullable=False)
    win_rate: Mapped[Decimal] = mapped_column(DECIMAL(5, 4), nullable=False)
    sharpe_ratio: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 4), nullable=True)
    total_trades: Mapped[int] = mapped_column(Integer, nullable=False)

    # Backtest parameters stored as JSON
    parameters_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<BacktestResult(id={self.id}, ticker={self.ticker}, "
            f"market={self.market}, total_return_pct={self.total_return_pct})>"
        )