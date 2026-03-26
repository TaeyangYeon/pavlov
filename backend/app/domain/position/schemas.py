from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PositionEntry(BaseModel):
    """Position entry representing a single buy transaction."""
    
    price: Decimal = Field(description="Entry price", gt=0, examples=[Decimal("100.50")])
    quantity: Decimal = Field(description="Quantity purchased", gt=0, examples=[Decimal("10")])
    entered_at: datetime = Field(description="Entry timestamp", examples=[datetime.now()])

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class PositionCreate(BaseModel):
    """Schema for creating a new position."""
    
    ticker: str = Field(description="Stock ticker symbol", min_length=1, max_length=10, examples=["AAPL", "005930"])
    market: str = Field(description="Market identifier", pattern="^(KR|US)$", examples=["US", "KR"])
    entries: List[PositionEntry] = Field(description="List of position entries", min_items=1)

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class PositionResponse(BaseModel):
    """Schema for position response data."""
    
    id: UUID = Field(description="Position unique identifier")
    ticker: str = Field(description="Stock ticker symbol")
    market: str = Field(description="Market identifier")
    entries: List[PositionEntry] = Field(description="List of position entries")
    avg_price: Optional[Decimal] = Field(description="Calculated average price", examples=[Decimal("102.50")])
    status: str = Field(description="Position status", examples=["open", "closed"])
    created_at: datetime = Field(description="Position creation timestamp")
    updated_at: datetime = Field(description="Position last update timestamp")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }
        from_attributes = True  # Pydantic v2 equivalent of orm_mode


class PositionUpdate(BaseModel):
    """Schema for updating an existing position."""
    
    entries: Optional[List[PositionEntry]] = Field(description="Updated list of position entries", default=None)
    avg_price: Optional[Decimal] = Field(description="Updated average price", default=None)
    status: Optional[str] = Field(description="Updated position status", pattern="^(open|closed)$", default=None)

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }