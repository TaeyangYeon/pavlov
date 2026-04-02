from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, Text, func, DECIMAL
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as SQLAlchemyUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class MarketEnum(StrEnum):
    """Market enumeration for KR (Korea) and US markets."""

    KR = "KR"
    US = "US"


class AnalysisLog(Base):
    """Analysis log model for tracking AI analysis execution."""

    __tablename__ = "analysis_log"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Analysis date
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Market being analyzed
    market: Mapped[MarketEnum] = mapped_column(
        SQLAlchemyEnum(MarketEnum, name="market_enum"), nullable=False
    )

    # CRITICAL for Step 17: Missed Execution Recovery
    # This flag determines whether the analysis was successfully executed
    executed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )

    # AI response data (nullable - may be empty if execution failed)
    ai_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Error message if execution failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AI cost tracking (Step 26: Performance Optimization)
    ai_cost_usd: Mapped[Decimal | None] = mapped_column(
        DECIMAL(8, 6), nullable=True
    )
    # Estimated cost in USD based on token usage
    # input_tokens * $3/1M + output_tokens * $15/1M

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<AnalysisLog(id={self.id}, date={self.date}, "
            f"market={self.market}, executed={self.executed})>"
        )
