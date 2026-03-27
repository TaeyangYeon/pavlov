"""
FilterPort interface for stock filtering operations.
Follows ABC pattern for SOLID Dependency Inversion principle.
"""

from abc import ABC, abstractmethod


class FilterPort(ABC):
    """Abstract interface for stock filtering operations."""

    @abstractmethod
    def apply(self, stocks: list[dict]) -> list[dict]:
        """
        Apply filter to list of stocks.

        Args:
            stocks: List of stock data dictionaries

        Returns:
            Filtered list of stocks
        """
        pass

    @property
    @abstractmethod
    def filter_name(self) -> str:
        """
        Get the name of this filter.

        Returns:
            Human-readable filter name
        """
        pass
