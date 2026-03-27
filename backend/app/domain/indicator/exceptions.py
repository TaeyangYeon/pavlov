"""
Custom exceptions for indicator calculations.
"""


class InsufficientDataError(Exception):
    """Raised when OHLCV data has fewer candles than required."""

    def __init__(self, indicator_name: str, required: int, actual: int):
        self.indicator_name = indicator_name
        self.required = required
        self.actual = actual
        super().__init__(f"{indicator_name} requires {required} candles, got {actual}")
