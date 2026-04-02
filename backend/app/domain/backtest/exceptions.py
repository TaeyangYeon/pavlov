"""Backtest domain exceptions."""

from decimal import Decimal

from app.domain.shared.exceptions import PavlovBaseException


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


class InsufficientCapitalError(BacktestException):
    """Raised when trying to buy with insufficient cash."""

    def __init__(self, required: Decimal, available: Decimal):
        super().__init__(
            f"Insufficient capital: need {required}, have {available}",
            code="INSUFFICIENT_CAPITAL",
        )


class InsufficientPositionError(BacktestException):
    """Raised when trying to sell more shares than available."""

    def __init__(self, ticker: str, required: Decimal, available: Decimal):
        super().__init__(
            f"Insufficient {ticker}: need {required}, have {available}",
            code="INSUFFICIENT_POSITION",
        )