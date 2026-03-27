"""
Moving Average alignment filter implementation.
Filters stocks based on bullish or bearish MA alignment.
"""

from app.domain.filter.interfaces import FilterPort


class MAAlignmentFilter(FilterPort):
    """Filter stocks by MA alignment (bullish or bearish trends)."""

    @property
    def filter_name(self) -> str:
        """Return filter name for identification."""
        return "ma_alignment_filter"

    def apply(self, stocks: list[dict]) -> list[dict]:
        """
        Filter stocks by MA alignment.

        Accepts:
        - Bullish: close > ma_20 > ma_60
        - Bearish: close < ma_20 < ma_60

        Rejects:
        - Sideways/mixed: any other combination

        Args:
            stocks: List of stock dictionaries from IndicatorEngine

        Returns:
            List of stocks that pass MA alignment filter

        Pure function: no side effects, does not mutate input.
        Fails safely on missing keys.
        """
        result = []
        for stock in stocks:
            try:
                close = stock["close"]
                ma_20 = stock["ma_20"]
                ma_60 = stock["ma_60"]

                # Check for clear trends
                bullish = close > ma_20 > ma_60
                bearish = close < ma_20 < ma_60

                if bullish or bearish:
                    result.append(stock)
            except KeyError:
                # Fail safely - missing required keys
                pass
        return result
