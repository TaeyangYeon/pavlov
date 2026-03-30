from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import ENUM as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID as SQLAlchemyUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class NotificationTypeEnum(StrEnum):
    STRATEGY_CHANGE = "strategy_change"
    TP_SL_ALERT = "tp_sl_alert"
    IMPULSE_WARNING = "impulse_warning"
    SYSTEM = "system"


class Notification(Base):
    """Notification model for in-app and email alerts."""

    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID | None] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=True
    )
    type: Mapped[NotificationTypeEnum] = mapped_column(
        SQLAlchemyEnum(NotificationTypeEnum,
                       name="notification_type_enum"),
        nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    body: Mapped[str] = mapped_column(
        String(500), nullable=False
    )
    ticker: Mapped[str | None] = mapped_column(
        String(10), nullable=True, index=True
    )
    action: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<Notification(id={self.id}, type={self.type}, "
            f"title={self.title[:30]}{'...' if len(self.title) > 30 else ''}, "
            f"is_read={self.is_read})>"
        )