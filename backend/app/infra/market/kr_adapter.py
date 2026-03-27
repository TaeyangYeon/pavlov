"""
Korean market data adapter using pykrx.
Implements MarketDataPort interface with async wrapper around sync pykrx library.
"""

import asyncio
from datetime import date

import pykrx.stock

from app.domain.market import MarketDataFetchError, MarketDataPort


class KRMarketAdapter(MarketDataPort):
    """
    Korean market data adapter using pykrx library.
    Wraps sync pykrx calls with async/await pattern.
    """

    async def fetch_daily_ohlcv(
        self, ticker: str, market: str, date_param: date
    ) -> dict | None:
        """
        Fetch single stock OHLCV from KRX via pykrx.
        Returns None for holidays/weekends/no data.
        Raises MarketDataFetchError on network failure.
        """
        try:
            # Convert date to string format for pykrx
            date_str = date_param.strftime("%Y%m%d")

            # Wrap sync pykrx call with run_in_executor
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                pykrx.stock.get_market_ohlcv_by_date,
                date_str,
                date_str,
                ticker,
            )

            # Handle empty DataFrame (no trading data)
            if df.empty:
                return None

            # Extract first (and only) row of data
            row = df.iloc[0]

            # Normalize to standard dict format
            return {
                "ticker": ticker,
                "market": market,
                "date": date_param.strftime("%Y-%m-%d"),
                "open": float(row["시가"]),
                "high": float(row["고가"]),
                "low": float(row["저가"]),
                "close": float(row["종가"]),
                "volume": int(row["거래량"]),
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
        """Check if KR market is open (weekday only for now)."""
        # Step 16 will add holiday calendar
        # For now: Mon-Fri = True, Sat-Sun = False
        today = date.today()
        return today.weekday() < 5  # 0=Monday, 4=Friday, 5=Saturday, 6=Sunday
