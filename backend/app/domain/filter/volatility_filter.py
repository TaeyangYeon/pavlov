"""
Volatility filter implementation.
Filters stocks based on ATR/close ratio within acceptable range.
"""

from app.domain.filter.exceptions import FilterConfigError
from app.domain.filter.interfaces import FilterPort


class VolatilityFilter(FilterPort):
    """Filter stocks by volatility (ATR/close ratio) range."""

    def __init__(self, min_atr_ratio: float = 0.005, max_atr_ratio: float = 0.05):
        """
        Initialize VolatilityFilter.

        Args:
            min_atr_ratio: Minimum ATR/close ratio (default 0.005 = 0.5%)
            max_atr_ratio: Maximum ATR/close ratio (default 0.05 = 5%)

        Raises:
            FilterConfigError: If min_atr_ratio >= max_atr_ratio
        """
        if min_atr_ratio >= max_atr_ratio:
            raise FilterConfigError(
                "volatility_filter",
                f"min_atr_ratio ({min_atr_ratio}) must be "
                f"less than max_atr_ratio ({max_atr_ratio})",
            )
        self._min = min_atr_ratio
        self._max = max_atr_ratio

    @property
    def filter_name(self) -> str:
        """Return filter name for identification."""
        return "volatility_filter"

    def apply(self, stocks: list[dict]) -> list[dict]:
        """
        Filter stocks by volatility range.

        Args:
            stocks: List of stock dictionaries from IndicatorEngine

        Returns:
            List of stocks that pass volatility filter

        Pure function: no side effects, does not mutate input.
        Fails safely on missing keys or zero close price.
        """
        result = []
        for stock in stocks:
            try:
                atr_14 = stock["atr_14"]
                close = stock["close"]
                atr_ratio = atr_14 / close
                if self._min <= atr_ratio <= self._max:
                    result.append(stock)
            except (KeyError, ZeroDivisionError):
                # Fail safely - missing keys or zero close price
                pass
        return result
