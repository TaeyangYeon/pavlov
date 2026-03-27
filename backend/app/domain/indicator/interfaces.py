"""
IndicatorPort interface for technical indicator calculations.
Follows ABC pattern for SOLID Dependency Inversion principle.
"""

from abc import ABC, abstractmethod


class IndicatorPort(ABC):
    """Abstract interface for technical indicator calculations."""

    @abstractmethod
    def calculate(self, ohlcv_data: list[dict]) -> dict:
        """
        Calculate indicator from OHLCV data.

        Args:
            ohlcv_data: List of OHLCV data dictionaries

        Returns:
            Dictionary with indicator results
        """
        pass

    @property
    @abstractmethod
    def indicator_name(self) -> str:
        """
        Get the name of this indicator.

        Returns:
            Human-readable indicator name
        """
        pass
