from datetime import date
from typing import List, Literal
from pydantic import BaseModel, Field, field_validator


class StockIndicators(BaseModel):
    """Stock with calculated technical indicators"""
    ticker: str = Field(description="Stock ticker symbol", examples=["AAPL", "GOOGL"])
    name: str = Field(description="Company name", examples=["Apple Inc.", "Alphabet Inc."])
    market: str = Field(description="Market exchange", examples=["NASDAQ", "NYSE"])
    close: float = Field(description="Current close price", gt=0, examples=[150.0, 2800.0])
    volume_ratio: float = Field(description="Volume ratio vs average", gt=0, examples=[1.5, 0.8])
    rsi_14: float = Field(description="14-period RSI indicator", ge=0, le=100, examples=[65.0, 35.0])
    ma_20: float = Field(description="20-period moving average", gt=0, examples=[145.0, 2750.0])
    ma_60: float = Field(description="60-period moving average", gt=0, examples=[140.0, 2700.0])
    atr_14: float = Field(description="14-period ATR indicator", gt=0, examples=[2.5, 50.0])


class HeldPosition(BaseModel):
    """Currently held stock position"""
    ticker: str = Field(description="Stock ticker symbol", examples=["AAPL", "MSFT"])
    avg_price: float = Field(description="Average purchase price", gt=0, examples=[140.0, 300.0])
    quantity: int = Field(description="Number of shares held", gt=0, examples=[100, 50])
    current_pnl_pct: float = Field(description="Current P&L percentage", examples=[7.14, -2.5])


class AIPromptInput(BaseModel):
    """Complete input data for AI analysis"""
    market: str = Field(description="Target market for analysis", examples=["NASDAQ", "NYSE"])
    date: str = Field(description="Analysis date", examples=["2024-01-01", "2024-12-31"])
    filtered_stocks: List[StockIndicators] = Field(description="Stocks that passed technical filters")
    held_positions: List[HeldPosition] = Field(description="Currently held positions")


class TakeProfitLevel(BaseModel):
    """Take profit level definition"""
    pct: float = Field(description="Profit percentage target", gt=0, examples=[5.0, 10.0, 15.0])
    sell_ratio: float = Field(description="Portion to sell at this level", gt=0, le=1.0, examples=[0.3, 0.5, 1.0])


class StopLossLevel(BaseModel):
    """Stop loss level definition"""
    pct: float = Field(description="Loss percentage threshold", lt=0, examples=[-3.0, -5.0, -10.0])
    sell_ratio: float = Field(description="Portion to sell at this level", gt=0, le=1.0, examples=[1.0, 0.5])


class StockStrategy(BaseModel):
    """AI-generated strategy for a single stock"""
    ticker: str = Field(description="Stock ticker symbol", examples=["AAPL", "GOOGL"])
    action: Literal["hold", "buy", "partial_sell", "full_exit"] = Field(
        description="Recommended action"
    )
    take_profit: List[TakeProfitLevel] = Field(description="Take profit levels")
    stop_loss: List[StopLossLevel] = Field(description="Stop loss levels")
    rationale: str = Field(description="Brief reasoning for the strategy", max_length=100)
    confidence: float = Field(description="Confidence score", ge=0.0, le=1.0, examples=[0.8, 0.6])


class AIPromptOutput(BaseModel):
    """Complete AI analysis output"""
    market_summary: str = Field(description="Overall market assessment", max_length=200)
    strategies: List[StockStrategy] = Field(description="Individual stock strategies")


class ValidationResult(BaseModel):
    """Validation result container"""
    is_valid: bool = Field(description="Whether validation passed")
    errors: List[str] = Field(description="List of validation error messages", default_factory=list)