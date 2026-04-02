from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.shared.exceptions import PavlovBaseException

BACKTEST_DISCLAIMER = (
    "⚠️ 과거 성과는 미래 수익을 보장하지 않습니다. "
    "이 백테스트 결과는 참고용이며, "
    "실제 투자 결과와 다를 수 있습니다."
)


@dataclass
class BacktestTrade:
    """Single trade executed during backtest."""

    date: date
    ticker: str
    action: str  # "buy" | "sell"
    quantity: Decimal
    price: Decimal  # execution price (next day open)
    pnl: Decimal  # realized P&L (0 for buys)
    trigger: str  # "signal" | "tp" | "sl" | "eod"
    holding_days: int  # days held before this sell


@dataclass
class DailyValue:
    """Portfolio value snapshot for one day."""

    date: date
    portfolio_value: Decimal
    cash: Decimal
    position_value: Decimal
    daily_return_pct: Decimal


@dataclass
class BacktestMetrics:
    """Performance metrics for a backtest run."""

    total_return_pct: Decimal
    max_drawdown_pct: Decimal
    win_rate: Decimal  # 0.0 ~ 1.0
    total_trades: int
    winning_trades: int
    losing_trades: int
    sharpe_ratio: Decimal | None
    best_day_pct: Decimal
    worst_day_pct: Decimal
    avg_holding_days: Decimal


@dataclass
class BacktestRunResult:
    """Complete result of a backtest simulation."""

    ticker: str
    market: str
    start_date: date
    end_date: date
    initial_capital: Decimal
    final_capital: Decimal
    metrics: BacktestMetrics
    trades: list[BacktestTrade]
    daily_values: list[DailyValue]
    disclaimer: str = field(default=BACKTEST_DISCLAIMER)


class BacktestRequest(BaseModel):
    """API request to run a backtest."""

    ticker: str = Field(min_length=1, max_length=10)
    market: str = Field(pattern="^(KR|US)$")
    start_date: date
    end_date: date
    initial_capital: Decimal = Field(
        default=Decimal("10000000"), gt=0, description="Initial capital in KRW/USD"
    )
    quantity_per_trade: Decimal = Field(
        default=Decimal("10"), gt=0, description="Fixed shares per trade"
    )
    take_profit_levels: list[dict] = Field(
        default_factory=lambda: [
            {"pct": 10.0, "sell_ratio": 0.5},
            {"pct": 20.0, "sell_ratio": 1.0},
        ]
    )
    stop_loss_levels: list[dict] = Field(
        default_factory=lambda: [
            {"pct": -5.0, "sell_ratio": 0.5},
            {"pct": -10.0, "sell_ratio": 1.0},
        ]
    )


class BacktestResponse(BaseModel):
    """API response for backtest results."""

    id: UUID | None = None
    ticker: str
    market: str
    start_date: date
    end_date: date
    initial_capital: str
    final_capital: str
    total_return_pct: str
    max_drawdown_pct: str
    win_rate: str
    win_rate_pct: str  # "65.0%"
    sharpe_ratio: str | None
    total_trades: int
    winning_trades: int
    losing_trades: int
    best_day_pct: str
    worst_day_pct: str
    avg_holding_days: str
    trades: list[dict]
    daily_values: list[dict]
    disclaimer: str
    created_at: str | None = None


class BacktestException(PavlovBaseException):
    """Base exception for backtest-related errors."""

    pass


class InsufficientHistoryError(BacktestException):
    """Raised when there's insufficient historical data for backtesting."""

    def __init__(self, ticker: str, required: int, available: int):
        super().__init__(
            f"{ticker}: insufficient history "
            f"(required {required}, available {available})",
            code="INSUFFICIENT_HISTORY",
        )