"""
ATR (Average True Range) indicator implementation.
Uses True Range calculation with Wilder's smoothing method for 14-period ATR.
"""

import pandas as pd

from app.domain.indicator.exceptions import InsufficientDataError
from app.domain.indicator.interfaces import IndicatorPort


class ATRIndicator(IndicatorPort):
    """ATR indicator with Wilder's smoothing method."""

    PERIOD = 14
    MIN_CANDLES = PERIOD + 1  # 15

    @property
    def indicator_name(self) -> str:
        return "atr_14"

    def calculate(self, ohlcv_data: list[dict]) -> dict:
        """
        Calculate 14-period ATR using True Range and Wilder's smoothing.

        Args:
            ohlcv_data: List of OHLCV dictionaries (oldest first, newest last)

        Returns:
            Dictionary with atr_14 value

        Raises:
            InsufficientDataError: If less than 15 candles provided
        """
        if len(ohlcv_data) < self.MIN_CANDLES:
            raise InsufficientDataError(
                self.indicator_name, self.MIN_CANDLES, len(ohlcv_data)
            )

        # Extract OHLC data as pandas Series
        highs = pd.Series([d["high"] for d in ohlcv_data])
        lows = pd.Series([d["low"] for d in ohlcv_data])
        closes = pd.Series([d["close"] for d in ohlcv_data])

        # Calculate True Range components
        # TR = max(high-low, abs(high-prev_close), abs(low-prev_close))
        prev_close = closes.shift(1)

        tr1 = highs - lows  # High - Low
        tr2 = (highs - prev_close).abs()  # abs(High - Previous Close)
        tr3 = (lows - prev_close).abs()   # abs(Low - Previous Close)

        # True Range is the maximum of the three
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Apply Wilder's smoothing (exponential moving average)
        # alpha = 1/period for Wilder's smoothing
        atr = true_range.ewm(
            alpha=1 / self.PERIOD, min_periods=self.PERIOD, adjust=False
        ).mean()

        # Return the most recent ATR value
        return {"atr_14": round(float(atr.iloc[-1]), 2)}
