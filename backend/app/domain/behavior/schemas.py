"""
Behavioral analysis schemas and dataclasses for emotional suppression system.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


@dataclass
class CoolingOffResult:
    """Result of cooling-off period check."""
    is_within_cooling_off: bool
    minutes_elapsed: float
    minutes_remaining: float
    cooling_off_minutes: int
    last_alert_time: datetime | None
    last_ai_recommendation: str | None
    ticker: str


@dataclass
class ImpulsePattern:
    """Detected impulse trading pattern."""
    pattern_type: str  # "rapid_reversal" | "ai_contradiction" | "overtrading"
    ticker: str
    detected_at: datetime
    description: str


@dataclass
class BehaviorReport:
    """Complete behavioral analysis report for a user."""
    user_id: str
    analysis_period_days: int
    total_trades: int
    ai_alignment_rate: float      # 0.0 ~ 1.0
    ai_aligned_count: int
    ai_contradicted_count: int
    no_ai_data_count: int
    impulse_trade_count: int
    contradiction_count: int
    overtrading_tickers: list[str]
    avg_holding_days: float
    most_traded_ticker: str | None
    cooling_off_warnings_received: int
    patterns: list[ImpulsePattern]
    generated_at: datetime


class DecisionCreate(BaseModel):
    """API request to record a user trading decision."""
    ticker: str = Field(min_length=1, max_length=10)
    market: str = Field(pattern="^(KR|US)$")
    action: str = Field(pattern="^(buy|sell|hold)$")
    price: Decimal = Field(gt=0)
    quantity: Decimal = Field(gt=0)
    notes: str | None = Field(default=None, max_length=500)
    override_cooling_off: bool = Field(default=False)


class DecisionResponse(BaseModel):
    """API response after recording a decision."""
    id: UUID
    ticker: str
    action: str
    price: Decimal
    quantity: Decimal
    ai_suggested: bool
    cooling_off_warning: bool
    notes: str | None
    created_at: datetime


class BehaviorReportResponse(BaseModel):
    """API response for behavior analysis."""
    total_trades: int
    ai_alignment_rate: float
    ai_alignment_pct: str   # "75.0%"
    alignment_label: str    # "가끔 AI와 다른 판단..."
    alignment_color: str    # "green" | "yellow" | ...
    impulse_trade_count: int
    contradiction_count: int
    overtrading_tickers: list[str]
    avg_holding_days: float
    most_traded_ticker: str | None
    cooling_off_warnings_received: int
    patterns: list[dict]
    analysis_period_days: int
    generated_at: str