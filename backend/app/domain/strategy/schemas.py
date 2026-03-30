"""
Unified strategy schemas for merging AI and position engine results.
Final output schemas for strategy integration engine.
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.ai.schemas import StockStrategy
from app.domain.position.schemas import (
    TpSlEvaluationResponse,
    TrailingStopEvaluationResponse,
)

ACTION_SEVERITY = {
    "hold": 0,
    "buy": 1,
    "partial_sell": 2,
    "full_exit": 3,
}


class UnifiedStrategy(BaseModel):
    """Final merged strategy output per ticker."""

    ticker: str = Field(description="Stock ticker symbol")
    market: str = Field(description="Market (KR/US)")
    final_action: str = Field(
        description="Final action: hold|buy|partial_sell|full_exit"
    )
    action_source: str = Field(description="Action source: ai|position_engine|merged")
    ai_strategy: StockStrategy | None = Field(
        default=None, description="Original AI strategy"
    )
    tp_sl_result: TpSlEvaluationResponse | None = Field(
        default=None, description="TP/SL engine result"
    )
    trailing_result: TrailingStopEvaluationResponse | None = Field(
        default=None, description="Trailing stop engine result"
    )
    confidence: Decimal = Field(description="Strategy confidence (0.0-1.0)")
    rationale: str = Field(max_length=200, description="Combined reasoning")
    sell_quantity: Decimal = Field(
        default=Decimal("0.0000"), description="Quantity to sell"
    )
    realized_pnl_estimate: Decimal = Field(
        default=Decimal("0.0000"), description="Estimated realized P&L"
    )
    changed_from_last: bool = Field(
        default=False, description="Changed from last strategy"
    )

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


class StrategyRunResult(BaseModel):
    """Complete strategy run output for one market."""

    market: str = Field(description="Market (KR/US)")
    run_date: date = Field(description="Analysis date")
    strategies: list[UnifiedStrategy] = Field(description="All ticker strategies")
    total_tickers_analyzed: int = Field(description="Number of tickers analyzed")
    changed_count: int = Field(description="Number of strategies that changed")
    analysis_log_id: UUID | None = Field(default=None, description="Analysis log ID")

    class Config:
        json_encoders = {date: lambda v: v.isoformat()}
