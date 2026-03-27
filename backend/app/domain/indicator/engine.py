"""
Indicator Engine orchestrator.
Coordinates all 4 indicators and outputs data matching StockIndicators schema.
"""

from app.domain.indicator.atr import ATRIndicator
from app.domain.indicator.moving_average import MovingAverageIndicator
from app.domain.indicator.rsi import RSIIndicator
from app.domain.indicator.volume_ratio import VolumeRatioIndicator


class IndicatorEngine:
    """Orchestrates all technical indicators for a single stock."""

    def __init__(self):
        """Initialize all indicators."""
        self._indicators = [
            RSIIndicator(),
            MovingAverageIndicator(),
            ATRIndicator(),
            VolumeRatioIndicator(),
        ]

    def calculate_all(
        self, ticker: str, name: str, market: str, ohlcv_data: list[dict]
    ) -> dict:
        """
        Calculate all 4 indicators for a stock.

        Args:
            ticker: Stock ticker symbol
            name: Company name
            market: Market name (e.g., "NASDAQ")
            ohlcv_data: List of OHLCV dictionaries (oldest first, newest last)

        Returns:
            Dictionary with all indicator values matching StockIndicators schema

        Raises:
            InsufficientDataError: If any indicator lacks sufficient data
        """
        # Initialize result with basic stock info
        result = {
            "ticker": ticker,
            "name": name,
            "market": market,
            "close": ohlcv_data[-1]["close"],  # Most recent close price
        }

        # Calculate each indicator and merge results
        for indicator in self._indicators:
            indicator_result = indicator.calculate(ohlcv_data)
            result.update(indicator_result)

        return result
