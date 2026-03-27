"""
Volume ratio filter implementation.
Filters stocks based on minimum volume ratio threshold.
"""

from app.domain.filter.interfaces import FilterPort


class VolumeFilter(FilterPort):
    """Filter stocks by volume ratio threshold."""

    def __init__(self, min_volume_ratio: float = 1.3):
        """
        Initialize VolumeFilter.

        Args:
            min_volume_ratio: Minimum volume ratio threshold (default 1.3)
        """
        self._min_volume_ratio = min_volume_ratio

    @property
    def filter_name(self) -> str:
        """Return filter name for identification."""
        return "volume_filter"

    def apply(self, stocks: list[dict]) -> list[dict]:
        """
        Filter stocks by volume ratio.

        Args:
            stocks: List of stock dictionaries from IndicatorEngine

        Returns:
            List of stocks that pass volume ratio filter

        Pure function: no side effects, does not mutate input.
        """
        result = []
        for stock in stocks:
            volume_ratio = stock.get("volume_ratio")
            if volume_ratio is not None and volume_ratio >= self._min_volume_ratio:
                result.append(stock)
        return result
