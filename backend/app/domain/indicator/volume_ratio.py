"""
Volume Ratio indicator implementation.
Calculates the ratio of today's volume to 20-day average volume.
"""

import pandas as pd

from app.domain.indicator.exceptions import InsufficientDataError
from app.domain.indicator.interfaces import IndicatorPort


class VolumeRatioIndicator(IndicatorPort):
    """Volume ratio indicator comparing today's volume to 20-day average."""

    PERIOD = 20
    MIN_CANDLES = PERIOD + 1  # 21 (20 days for average + today)

    @property
    def indicator_name(self) -> str:
        return "volume_ratio"

    def calculate(self, ohlcv_data: list[dict]) -> dict:
        """
        Calculate volume ratio: today's volume / 20-day average volume.

        Args:
            ohlcv_data: List of OHLCV dictionaries (oldest first, newest last)

        Returns:
            Dictionary with volume_ratio value

        Raises:
            InsufficientDataError: If less than 21 candles provided
        """
        if len(ohlcv_data) < self.MIN_CANDLES:
            raise InsufficientDataError(
                self.indicator_name, self.MIN_CANDLES, len(ohlcv_data)
            )

        # Extract volume data as pandas Series
        volumes = pd.Series([d["volume"] for d in ohlcv_data])

        # Calculate 20-day moving average of volume
        # We need the average of the 20 days BEFORE today
        volume_avg_20 = volumes[:-1].rolling(
            window=self.PERIOD, min_periods=self.PERIOD
        ).mean()

        # Get today's volume (last volume) and the 20-day average
        today_volume = volumes.iloc[-1]
        avg_20_day_volume = volume_avg_20.iloc[-1]

        # Calculate the ratio
        volume_ratio = today_volume / avg_20_day_volume

        return {"volume_ratio": round(float(volume_ratio), 3)}
