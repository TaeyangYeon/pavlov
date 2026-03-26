from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import String, Date, BigInteger, UniqueConstraint, Enum as SQLAlchemyEnum, func, DECIMAL
from sqlalchemy.dialects.postgresql import UUID as SQLAlchemyUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class MarketEnum(str, Enum):
    """Market enumeration for KR (Korea) and US markets."""
    KR = "KR"
    US = "US"


class MarketData(Base):
    """Market data model for OHLCV daily candlestick data."""
    
    __tablename__ = "market_data"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Stock identification
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    market: Mapped[MarketEnum] = mapped_column(
        SQLAlchemyEnum(MarketEnum, name="market_enum"), 
        nullable=False
    )
    
    # Date for this market data
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    
    # OHLC data with high precision
    open: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), nullable=False)
    high: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), nullable=False)
    low: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), nullable=False)
    close: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), nullable=False)
    
    # Volume data
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    
    # Unique constraint: one record per ticker/market/date combination
    __table_args__ = (
        UniqueConstraint("ticker", "market", "date", name="uq_market_data_ticker_market_date"),
    )
    
    def __repr__(self) -> str:
        return f"<MarketData(id={self.id}, ticker={self.ticker}, market={self.market}, date={self.date}, close={self.close})>"