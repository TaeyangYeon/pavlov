"""
Market data exceptions.
Custom exceptions for market data adapter operations.
"""

from app.domain.shared.exceptions import ExternalServiceError


class MarketDataFetchError(ExternalServiceError):
    """Raised when market data cannot be fetched."""

    def __init__(self, ticker: str, market: str, reason: str):
        self.ticker = ticker
        self.market = market
        self.reason = reason
        super().__init__(
            service=f"{market}_market_data",
            reason=f"Failed to fetch data for {ticker}: {reason}",
            details={"ticker": ticker, "market": market}
        )
