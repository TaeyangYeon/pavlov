"""
RSI (Relative Strength Index) indicator implementation.
Uses Wilder's smoothing method for 14-period RSI calculation.
"""

import pandas as pd

from app.domain.indicator.exceptions import InsufficientDataError
from app.domain.indicator.interfaces import IndicatorPort


class RSIIndicator(IndicatorPort):
    """RSI indicator with Wilder's smoothing method."""

    PERIOD = 14
    MIN_CANDLES = PERIOD + 1  # 15

    @property
    def indicator_name(self) -> str:
        return "rsi_14"

    def calculate(self, ohlcv_data: list[dict]) -> dict:
        """
        Calculate 14-period RSI using Wilder's smoothing.

        Args:
            ohlcv_data: List of OHLCV dictionaries (oldest first, newest last)

        Returns:
            Dictionary with rsi_14 value

        Raises:
            InsufficientDataError: If less than 15 candles provided
        """
        if len(ohlcv_data) < self.MIN_CANDLES:
            raise InsufficientDataError(
                self.indicator_name, self.MIN_CANDLES, len(ohlcv_data)
            )

        # Extract close prices as pandas Series
        closes = pd.Series([d["close"] for d in ohlcv_data])

        # Calculate price changes (deltas)
        delta = closes.diff()

        # Separate gains and losses
        gain = delta.clip(lower=0)  # Positive changes only
        loss = -delta.clip(upper=0)  # Negative changes (made positive)

        # Apply Wilder's smoothing (exponential moving average)
        # alpha = 1/period for Wilder's smoothing
        avg_gain = gain.ewm(
            alpha=1 / self.PERIOD, min_periods=self.PERIOD, adjust=False
        ).mean()
        avg_loss = loss.ewm(
            alpha=1 / self.PERIOD, min_periods=self.PERIOD, adjust=False
        ).mean()

        # Calculate Relative Strength (RS) and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # Return the most recent RSI value
        return {"rsi_14": round(float(rsi.iloc[-1]), 2)}
