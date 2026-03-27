"""
Market data exceptions.
Custom exceptions for market data adapter operations.
"""


class MarketDataFetchError(Exception):
    """Raised when market data cannot be fetched."""

    def __init__(self, ticker: str, market: str, reason: str):
        self.ticker = ticker
        self.market = market
        self.reason = reason
        super().__init__(f"Failed to fetch {market} data for {ticker}: {reason}")
