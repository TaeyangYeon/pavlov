"""
Filter chain orchestrator implementation.
Applies multiple filters sequentially with logging.
"""

from app.domain.filter.interfaces import FilterPort
from app.domain.filter.ma_alignment_filter import MAAlignmentFilter
from app.domain.filter.volatility_filter import VolatilityFilter
from app.domain.filter.volume_filter import VolumeFilter


class FilterChain:
    """
    Applies multiple filters sequentially.
    Output of filter N becomes input of filter N+1.
    Single responsibility: orchestration only, no filter logic.
    """

    def __init__(self, filters: list[FilterPort]):
        """
        Initialize FilterChain.

        Args:
            filters: List of filters to apply in sequence
        """
        self._filters = filters
        self._filter_log: list[dict] = []

    def apply(self, stocks: list[dict]) -> list[dict]:
        """
        Apply all filters in sequence.
        Returns empty list if all stocks filtered out.

        Args:
            stocks: List of stock dictionaries

        Returns:
            List of stocks that pass all filters

        Pure function: no side effects, does not mutate input.
        """
        self._filter_log = []
        current = stocks

        for filter_instance in self._filters:
            before = len(current)
            current = filter_instance.apply(current)
            after = len(current)
            removed = before - after

            # Log filter application
            self._filter_log.append(
                {
                    "filter": filter_instance.filter_name,
                    "before": before,
                    "after": after,
                    "removed": removed,
                }
            )

            # Print progress (will be replaced with proper logging in Step 23)
            print(
                f"[FilterChain] {filter_instance.filter_name}: "
                f"{before} → {after} stocks "
                f"(removed {removed})"
            )

        return current

    @property
    def filter_log(self) -> list[dict]:
        """Returns log of each filter's pass/fail counts."""
        return self._filter_log.copy()  # Return copy to maintain immutability


def build_default_filter_chain() -> FilterChain:
    """
    Builds the default filter chain for pavlov.
    Order matters: cheapest filter first (volume),
    then volatility, then MA alignment.

    Returns:
        FilterChain with default filters configured
    """
    return FilterChain(
        [
            VolumeFilter(min_volume_ratio=1.3),
            VolatilityFilter(min_atr_ratio=0.005, max_atr_ratio=0.05),
            MAAlignmentFilter(),
        ]
    )
