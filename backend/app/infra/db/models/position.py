from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import String, ForeignKey, Enum as SQLAlchemyEnum, func, DECIMAL
from sqlalchemy.dialects.postgresql import JSONB, UUID as SQLAlchemyUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class MarketEnum(str, Enum):
    """Market enumeration for KR (Korea) and US markets."""
    KR = "KR"
    US = "US"


class PositionStatusEnum(str, Enum):
    """Position status enumeration."""
    OPEN = "open"
    CLOSED = "closed"


class Position(Base):
    """Position model for tracking user stock positions."""
    
    __tablename__ = "positions"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key to user
    user_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True), 
        ForeignKey("users.id"), 
        nullable=False,
        index=True
    )
    
    # Stock identification
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    market: Mapped[MarketEnum] = mapped_column(
        SQLAlchemyEnum(MarketEnum, name="market_enum"), 
        nullable=False
    )
    
    # Position entries as JSONB array
    # Format: [{"price": 100.0, "quantity": 10, "entered_at": "ISO datetime"}]
    entries: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    
    # Calculated average price (updated by application logic)
    avg_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4), nullable=True)
    
    # Position status
    status: Mapped[PositionStatusEnum] = mapped_column(
        SQLAlchemyEnum(PositionStatusEnum, name="position_status_enum"),
        default=PositionStatusEnum.OPEN,
        nullable=False
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<Position(id={self.id}, user_id={self.user_id}, ticker={self.ticker}, market={self.market}, status={self.status})>"