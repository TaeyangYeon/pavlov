from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DECIMAL, Boolean, ForeignKey, String, Text, func
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID as SQLAlchemyUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class DecisionActionEnum(StrEnum):
    """Decision action enumeration for user decisions."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class DecisionLog(Base):
    """Decision log model for tracking user investment decisions."""

    __tablename__ = "decision_log"

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

    # User's action
    action: Mapped[DecisionActionEnum] = mapped_column(
        SQLAlchemyEnum(DecisionActionEnum, name="decision_action_enum"), nullable=False
    )

    # Transaction details
    price: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), nullable=False)

    # AI recommendation tracking
    # This field is critical for emotional pattern analysis in future steps
    ai_suggested: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)

    # Optional user notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<DecisionLog(id={self.id}, user_id={self.user_id}, "
            f"ticker={self.ticker}, action={self.action}, "
            f"ai_suggested={self.ai_suggested})>"
        )
