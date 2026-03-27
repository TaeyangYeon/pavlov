"""
StrategyPort interface for investment strategy operations.
Follows ABC pattern for SOLID Dependency Inversion principle.
"""

from abc import ABC, abstractmethod
from datetime import date


class StrategyPort(ABC):
    """Abstract interface for investment strategy operations."""

    @abstractmethod
    async def generate(
        self,
        market: str,
        date: date,
        filtered_stocks: list[dict],
        held_positions: list[dict],
    ) -> dict:
        """
        Generate investment strategy for given inputs.

        Args:
            market: Market identifier (KR, US)
            date: Trading date
            filtered_stocks: List of stocks that passed filters
            held_positions: Currently held positions

        Returns:
            Strategy recommendation dictionary
        """
        pass

    @abstractmethod
    async def get_latest(self, market: str, date: date) -> dict | None:
        """
        Get latest strategy for market and date.

        Args:
            market: Market identifier
            date: Trading date

        Returns:
            Latest strategy or None if not found
        """
        pass
