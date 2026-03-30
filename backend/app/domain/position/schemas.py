from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.domain.ai.schemas import StopLossLevel, TakeProfitLevel


class PositionEntry(BaseModel):
    """Position entry representing a single buy transaction."""

    price: Decimal = Field(
        description="Entry price", gt=0, examples=[Decimal("100.50")]
    )
    quantity: Decimal = Field(
        description="Quantity purchased", gt=0, examples=[Decimal("10")]
    )
    entered_at: datetime = Field(
        description="Entry timestamp", examples=[datetime.now()]
    )

    class Config:
        json_encoders = {Decimal: lambda v: float(v), datetime: lambda v: v.isoformat()}


class PositionCreate(BaseModel):
    """Schema for creating a new position."""

    ticker: str = Field(
        description="Stock ticker symbol",
        min_length=1,
        max_length=10,
        examples=["AAPL", "005930"],
    )
    market: str = Field(
        description="Market identifier", pattern="^(KR|US)$", examples=["US", "KR"]
    )
    entries: list[PositionEntry] = Field(
        description="List of position entries", min_items=1
    )
    avg_price: Decimal | None = Field(
        description="Calculated average price", default=None
    )

    class Config:
        json_encoders = {Decimal: lambda v: float(v), datetime: lambda v: v.isoformat()}


class PositionResponse(BaseModel):
    """Schema for position response data."""

    id: UUID = Field(description="Position unique identifier")
    ticker: str = Field(description="Stock ticker symbol")
    market: str = Field(description="Market identifier")
    entries: list[PositionEntry] = Field(description="List of position entries")
    avg_price: Decimal | None = Field(
        description="Calculated average price", examples=[Decimal("102.50")]
    )
    status: str = Field(description="Position status", examples=["open", "closed"])
    created_at: datetime = Field(description="Position creation timestamp")
    updated_at: datetime = Field(description="Position last update timestamp")

    class Config:
        json_encoders = {Decimal: lambda v: float(v), datetime: lambda v: v.isoformat()}
        from_attributes = True  # Pydantic v2 equivalent of orm_mode


class PositionUpdate(BaseModel):
    """Schema for updating an existing position."""

    entries: list[PositionEntry] | None = Field(
        description="Updated list of position entries", default=None
    )
    avg_price: Decimal | None = Field(description="Updated average price", default=None)
    status: str | None = Field(
        description="Updated position status", pattern="^(open|closed)$", default=None
    )

    class Config:
        json_encoders = {Decimal: lambda v: float(v), datetime: lambda v: v.isoformat()}


@dataclass
class PnLResult:
    """Pure data class for PnL calculation results."""

    unrealized_pnl: Decimal
    unrealized_pnl_percent: Decimal
    realized_pnl: Decimal
    total_pnl: Decimal


class PositionWithPnL(BaseModel):
    """Position with calculated PnL data."""

    id: UUID = Field(description="Position unique identifier")
    ticker: str = Field(description="Stock ticker symbol")
    market: str = Field(description="Market identifier")
    entries: list[PositionEntry] = Field(description="List of position entries")
    avg_price: Decimal | None = Field(
        description="Calculated average price", examples=[Decimal("102.50")]
    )
    status: str = Field(description="Position status", examples=["open", "closed"])
    created_at: datetime = Field(description="Position creation timestamp")
    updated_at: datetime = Field(description="Position last update timestamp")
    current_price: Decimal = Field(description="Current market price")
    unrealized_pnl: Decimal = Field(description="Unrealized P&L amount")
    unrealized_pnl_percent: Decimal = Field(description="Unrealized P&L percentage")
    realized_pnl: Decimal = Field(description="Realized P&L amount")
    total_pnl: Decimal = Field(description="Total P&L (unrealized + realized)")

    class Config:
        json_encoders = {Decimal: lambda v: float(v), datetime: lambda v: v.isoformat()}
        from_attributes = True


@dataclass
class TpSlDecision:
    """Result of TP/SL judgment for a position."""
    action: str          # "hold" | "partial_sell" | "full_exit"
    triggered_by: str    # "tp" | "sl" | "none"
    triggered_level_pct: Decimal | None
    sell_quantity: Decimal
    sell_ratio: Decimal
    current_pnl_pct: Decimal
    realized_pnl_estimate: Decimal


class TpSlEvaluationRequest(BaseModel):
    """Input for TP/SL engine evaluation via API."""
    position_id: UUID
    current_price: Decimal = Field(gt=0)
    take_profit_levels: list[TakeProfitLevel] = Field(
        default_factory=list
    )
    stop_loss_levels: list[StopLossLevel] = Field(
        default_factory=list
    )


class TpSlEvaluationResponse(BaseModel):
    """API response for TP/SL evaluation."""
    position_id: UUID
    ticker: str
    action: str
    triggered_by: str
    triggered_level_pct: Decimal | None
    sell_quantity: Decimal
    sell_ratio: Decimal
    current_pnl_pct: Decimal
    realized_pnl_estimate: Decimal
    avg_price: Decimal
    current_price: Decimal
    total_quantity: Decimal

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


class TrailingStopConfig(BaseModel):
    """Configuration for trailing stop evaluation."""
    mode: Literal["percentage", "atr"] = "percentage"
    trail_pct: Decimal | None = Field(
        default=None,
        description="Trail distance as percentage (e.g. 10.0 = 10%)"
    )
    atr_multiplier: Decimal | None = Field(
        default=None,
        description="ATR multiplier (e.g. 2.0 = 2×ATR)"
    )
    atr_value: Decimal | None = Field(
        default=None,
        description="Current ATR value from IndicatorEngine"
    )

    @model_validator(mode="after")
    def validate_config(self):
        if self.mode == "percentage" and self.trail_pct is None:
            raise ValueError(
                "trail_pct required for percentage mode"
            )
        if self.mode == "atr" and (
            self.atr_multiplier is None
            or self.atr_value is None
        ):
            raise ValueError(
                "atr_multiplier and atr_value required "
                "for ATR mode"
            )
        return self


@dataclass
class TrailingStopResult:
    """Result of trailing stop evaluation."""
    triggered: bool
    action: str              # "full_exit" | "hold"
    high_water_mark: Decimal
    stop_price: Decimal
    current_price: Decimal
    trail_distance_pct: Decimal
    distance_to_stop_pct: Decimal


class TrailingStopEvaluationRequest(BaseModel):
    """API request for trailing stop evaluation."""
    position_id: UUID
    current_price: Decimal = Field(gt=0)
    config: TrailingStopConfig


class TrailingStopEvaluationResponse(BaseModel):
    """API response for trailing stop evaluation."""
    position_id: UUID
    ticker: str
    triggered: bool
    action: str
    high_water_mark: Decimal
    stop_price: Decimal
    current_price: Decimal
    trail_distance_pct: Decimal
    distance_to_stop_pct: Decimal
    new_high_water_mark: Decimal
    hwm_updated: bool

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}
