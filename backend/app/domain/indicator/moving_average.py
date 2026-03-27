"""
Moving Average indicator implementation.
Calculates both 20-period and 60-period simple moving averages.
"""

import pandas as pd

from app.domain.indicator.exceptions import InsufficientDataError
from app.domain.indicator.interfaces import IndicatorPort


class MovingAverageIndicator(IndicatorPort):
    """Moving average indicator with MA20 and MA60 calculation."""

    MA20_PERIOD = 20
    MA60_PERIOD = 60
    MIN_CANDLES = MA60_PERIOD  # 60 (determined by longest period)

    @property
    def indicator_name(self) -> str:
        return "moving_average"

    def calculate(self, ohlcv_data: list[dict]) -> dict:
        """
        Calculate 20-period and 60-period simple moving averages.

        Args:
            ohlcv_data: List of OHLCV dictionaries (oldest first, newest last)

        Returns:
            Dictionary with ma_20 and optionally ma_60 values

        Raises:
            InsufficientDataError: If less than 60 candles provided
        """
        if len(ohlcv_data) < self.MIN_CANDLES:
            raise InsufficientDataError(
                self.indicator_name, self.MIN_CANDLES, len(ohlcv_data)
            )

        # Extract close prices as pandas Series
        closes = pd.Series([d["close"] for d in ohlcv_data])

        # Calculate simple moving averages
        ma_20 = closes.rolling(
            window=self.MA20_PERIOD, min_periods=self.MA20_PERIOD
        ).mean()
        ma_60 = closes.rolling(
            window=self.MA60_PERIOD, min_periods=self.MA60_PERIOD
        ).mean()

        # Return the most recent MA values
        return {
            "ma_20": round(float(ma_20.iloc[-1]), 2),
            "ma_60": round(float(ma_60.iloc[-1]), 2),
        }
