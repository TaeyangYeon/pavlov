from datetime import datetime, date
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import String, Date, Boolean, Text, Enum as SQLAlchemyEnum, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as SQLAlchemyUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class MarketEnum(str, Enum):
    """Market enumeration for KR (Korea) and US markets."""
    KR = "KR"
    US = "US"


class AnalysisLog(Base):
    """Analysis log model for tracking AI analysis execution."""
    
    __tablename__ = "analysis_log"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Analysis date
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    
    # Market being analyzed
    market: Mapped[MarketEnum] = mapped_column(
        SQLAlchemyEnum(MarketEnum, name="market_enum"), 
        nullable=False
    )
    
    # CRITICAL for Step 17: Missed Execution Recovery
    # This flag determines whether the analysis was successfully executed
    executed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    
    # AI response data (nullable - may be empty if execution failed)
    ai_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    # Error message if execution failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<AnalysisLog(id={self.id}, date={self.date}, market={self.market}, executed={self.executed})>"