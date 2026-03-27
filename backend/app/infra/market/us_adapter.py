"""
US market data adapter using yfinance.
Implements MarketDataPort interface with async wrapper around sync yfinance library.
"""

import asyncio
from datetime import date

import pandas as pd
import yfinance

from app.domain.market import MarketDataFetchError, MarketDataPort


class USMarketAdapter(MarketDataPort):
    """
    US market data adapter using yfinance library.
    Wraps sync yfinance calls with async/await pattern.
    """

    async def fetch_daily_ohlcv(
        self, ticker: str, market: str, date_param: date
    ) -> dict | None:
        """
        Fetch single stock OHLCV from Yahoo Finance via yfinance.
        Normalizes ticker to uppercase.
        Returns None for no data/holidays.
        """
        try:
            # Normalize ticker to uppercase
            ticker_upper = ticker.upper()

            # Wrap sync yfinance call with run_in_executor
            loop = asyncio.get_event_loop()

            def _fetch_yfinance_data():
                ticker_obj = yfinance.Ticker(ticker_upper)
                # Fetch single day data
                return ticker_obj.history(
                    start=date_param, end=date_param + pd.Timedelta(days=1)
                )

            df = await loop.run_in_executor(None, _fetch_yfinance_data)

            # Handle empty DataFrame (no trading data)
            if df.empty:
                return None

            # Extract first (and only) row of data
            row = df.iloc[0]

            # Normalize to standard dict format
            return {
                "ticker": ticker_upper,
                "market": market,
                "date": date_param.strftime("%Y-%m-%d"),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]),
            }

        except Exception as e:
            # Never let raw library exceptions propagate
            raise MarketDataFetchError(ticker, market, str(e)) from e

    async def fetch_multiple(
        self, tickers: list[str], market: str, date_param: date
    ) -> list[dict]:
        """Fetch multiple tickers, skip failures silently."""
        results = []

        for ticker in tickers:
            try:
                result = await self.fetch_daily_ohlcv(ticker, market, date_param)
                if result is not None:
                    results.append(result)
            except MarketDataFetchError:
                # Skip failed tickers, don't crash entire operation
                continue

        return results

    async def is_market_open(self, market: str) -> bool:
        """Check if US market is open (weekday only for now)."""
        # Step 16 will add holiday calendar
        # For now: Mon-Fri = True, Sat-Sun = False
        today = date.today()
        return today.weekday() < 5  # 0=Monday, 4=Friday, 5=Saturday, 6=Sunday
