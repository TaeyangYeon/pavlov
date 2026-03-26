from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DECIMAL, ForeignKey, String, func
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as SQLAlchemyUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class MarketEnum(StrEnum):
    """Market enumeration for KR (Korea) and US markets."""

    KR = "KR"
    US = "US"


class PositionStatusEnum(StrEnum):
    """Position status enumeration."""

    OPEN = "open"
    CLOSED = "closed"


class Position(Base):
    """Position model for tracking user stock positions."""

    __tablename__ = "positions"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Foreign key to user
    user_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Stock identification
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    market: Mapped[MarketEnum] = mapped_column(
        SQLAlchemyEnum(MarketEnum, name="market_enum"), nullable=False
    )

    # Position entries as JSONB array
    # Format: [{"price": 100.0, "quantity": 10, "entered_at": "ISO datetime"}]
    entries: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )

    # Calculated average price (updated by application logic)
    avg_price: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 4), nullable=True)

    # Position status
    status: Mapped[PositionStatusEnum] = mapped_column(
        SQLAlchemyEnum(PositionStatusEnum, name="position_status_enum"),
        default=PositionStatusEnum.OPEN,
        nullable=False,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<Position(id={self.id}, user_id={self.user_id}, "
            f"ticker={self.ticker}, market={self.market}, status={self.status})>"
        )
