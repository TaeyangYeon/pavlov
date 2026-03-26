from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import String, ForeignKey, Text, Enum as SQLAlchemyEnum, func, DECIMAL
from sqlalchemy.dialects.postgresql import JSONB, UUID as SQLAlchemyUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class ActionEnum(str, Enum):
    """Action enumeration matching AI output schema."""
    HOLD = "hold"
    BUY = "buy"
    PARTIAL_SELL = "partial_sell"
    FULL_EXIT = "full_exit"


class StrategyOutput(Base):
    """Strategy output model for storing AI-generated strategies."""
    
    __tablename__ = "strategy_output"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key to analysis log
    analysis_log_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True), 
        ForeignKey("analysis_log.id"), 
        nullable=False,
        index=True
    )
    
    # Stock identification
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    
    # Recommended action
    action: Mapped[ActionEnum] = mapped_column(
        SQLAlchemyEnum(ActionEnum, name="action_enum"), 
        nullable=False
    )
    
    # Take profit levels as JSONB
    # Format: [{"pct": 5.0, "sell_ratio": 0.5}, {"pct": 10.0, "sell_ratio": 0.5}]
    take_profit_levels: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    
    # Stop loss levels as JSONB
    # Format: [{"pct": -3.0, "sell_ratio": 1.0}]
    stop_loss_levels: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    
    # Strategy rationale (max 100 chars as per AI schema)
    rationale: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Confidence score (0.0 to 1.0)
    confidence: Mapped[Decimal] = mapped_column(DECIMAL(3, 2), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<StrategyOutput(id={self.id}, analysis_log_id={self.analysis_log_id}, ticker={self.ticker}, action={self.action}, confidence={self.confidence})>"