"""
Korean market data adapter using pykrx.
Implements MarketDataPort interface with async wrapper around sync pykrx library.
"""

import asyncio
from datetime import date
from typing import Any

import pykrx.stock

from app.domain.market import MarketDataFetchError, MarketDataPort
from app.domain.market.validator import MarketDataValidator
from app.domain.shared.result import Result


class KRMarketAdapter(MarketDataPort):
    """
    Korean market data adapter using pykrx library.
    Wraps sync pykrx calls with async/await pattern.
    Includes timeout and validation for production resilience.
    """

    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds
        self.validator = MarketDataValidator()

    async def fetch_daily_ohlcv(
        self, ticker: str, market: str, date_param: date
    ) -> dict | None:
        """
        Fetch single stock OHLCV from KRX via pykrx.
        Returns None for holidays/weekends/no data.
        Raises MarketDataFetchError on network failure or timeout.
        """
        try:
            # Convert date to string format for pykrx
            date_str = date_param.strftime("%Y%m%d")

            # Wrap sync pykrx call with run_in_executor and timeout
            loop = asyncio.get_event_loop()
            df = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    pykrx.stock.get_market_ohlcv_by_date,
                    date_str,
                    date_str,
                    ticker,
                ),
                timeout=self.timeout_seconds
            )

            # Handle empty DataFrame (no trading data)
            if df.empty:
                return None

            # Extract first (and only) row of data
            row = df.iloc[0]

            # Create raw data dict
            raw_data = {
                "ticker": ticker,
                "market": market,
                "date": date_param.strftime("%Y-%m-%d"),
                "open": float(row["시가"]),
                "high": float(row["고가"]),
                "low": float(row["저가"]),
                "close": float(row["종가"]),
                "volume": int(row["거래량"]),
            }

            # Validate and sanitize data
            validated_data = self.validator.validate(raw_data)
            return validated_data

        except TimeoutError:
            raise MarketDataFetchError(
                ticker, market, f"Timeout after {self.timeout_seconds}s"
            )
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

    async def fetch_daily_ohlcv_safe(
        self, ticker: str, market: str, date_param: date
    ) -> Result[dict[str, Any]]:
        """
        Safe version of fetch_daily_ohlcv using Result pattern.
        Returns Result[Dict] instead of raising exceptions.
        Useful for fallback strategies and error handling.
        """
        try:
            data = await self.fetch_daily_ohlcv(ticker, market, date_param)
            if data is None:
                return Result.fail(f"No data available for {ticker} on {date_param}")
            return Result.ok(data)
        except MarketDataFetchError as e:
            return Result.fail(f"Market data fetch failed: {e.reason}")
        except Exception as e:
            return Result.fail(f"Unexpected error: {str(e)}")
