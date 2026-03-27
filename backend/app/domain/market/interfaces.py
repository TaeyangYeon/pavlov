"""
MarketDataPort interface for abstracting market data sources.
Follows ABC pattern for SOLID Dependency Inversion principle.
"""

from abc import ABC, abstractmethod
from datetime import date


class MarketDataPort(ABC):
    """Abstract interface for market data operations."""

    @abstractmethod
    async def fetch_daily_ohlcv(
        self, ticker: str, market: str, date: date
    ) -> dict | None:
        """
        Fetch daily OHLCV data for a specific ticker.

        Args:
            ticker: Stock ticker symbol
            market: Market identifier (KR, US)
            date: Trading date

        Returns:
            Dict with OHLCV data or None if not found
        """
        pass

    @abstractmethod
    async def fetch_multiple(
        self, tickers: list[str], market: str, date: date
    ) -> list[dict]:
        """
        Fetch OHLCV data for multiple tickers.

        Args:
            tickers: List of ticker symbols
            market: Market identifier
            date: Trading date

        Returns:
            List of OHLCV data dicts
        """
        pass

    @abstractmethod
    async def is_market_open(self, market: str) -> bool:
        """
        Check if market is currently open for trading.

        Args:
            market: Market identifier

        Returns:
            True if market is open
        """
        pass
