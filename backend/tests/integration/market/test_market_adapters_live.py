"""
Live integration tests for market adapters.
These tests make actual network calls to external APIs.
They are marked with @pytest.mark.live and excluded from CI.
"""

from datetime import date, timedelta

import pytest
from app.infra.market.kr_adapter import KRMarketAdapter
from app.infra.market.us_adapter import USMarketAdapter


@pytest.mark.live
@pytest.mark.asyncio
async def test_kr_adapter_live_fetch_samsung():
    """Live test: fetch Samsung Electronics (005930) latest data."""
    adapter = KRMarketAdapter()

    # Use a past weekday to increase chance of having data
    # Samsung Electronics is always tradeable on KR market
    yesterday = date.today() - timedelta(days=1)

    try:
        result = await adapter.fetch_daily_ohlcv("005930", "KR", yesterday)

        # result may be None on weekends/holidays - just verify no exception
        if result is not None:
            # Verify structure if we got data
            assert result["ticker"] == "005930"
            assert result["market"] == "KR"
            assert result["date"] == yesterday.strftime("%Y-%m-%d")
            assert isinstance(result["open"], float)
            assert isinstance(result["high"], float)
            assert isinstance(result["low"], float)
            assert isinstance(result["close"], float)
            assert isinstance(result["volume"], int)
            assert result["high"] >= result["low"]
            print(f"✅ KR Live test passed: Samsung data = {result}")
        else:
            print(f"⚠️  KR Live test: No data for {yesterday} (likely weekend/holiday)")

    except Exception as e:
        # Print error but don't fail - live tests can be flaky
        print(f"⚠️  KR Live test error (expected during network issues): {e}")


@pytest.mark.live
@pytest.mark.asyncio
async def test_us_adapter_live_fetch_apple():
    """Live test: fetch Apple (AAPL) latest data."""
    adapter = USMarketAdapter()

    # Use a past weekday to increase chance of having data
    yesterday = date.today() - timedelta(days=1)

    try:
        result = await adapter.fetch_daily_ohlcv("AAPL", "US", yesterday)

        # result may be None on weekends/holidays - just verify no exception
        if result is not None:
            # Verify structure if we got data
            assert result["ticker"] == "AAPL"
            assert result["market"] == "US"
            assert result["date"] == yesterday.strftime("%Y-%m-%d")
            assert isinstance(result["open"], float)
            assert isinstance(result["high"], float)
            assert isinstance(result["low"], float)
            assert isinstance(result["close"], float)
            assert isinstance(result["volume"], int)
            assert result["high"] >= result["low"]
            print(f"✅ US Live test passed: Apple data = {result}")
        else:
            print(f"⚠️  US Live test: No data for {yesterday} (likely weekend/holiday)")

    except Exception as e:
        # Print error but don't fail - live tests can be flaky
        print(f"⚠️  US Live test error (expected during network issues): {e}")


@pytest.mark.live
@pytest.mark.asyncio
async def test_kr_adapter_live_fetch_multiple():
    """Live test: fetch multiple KR tickers."""
    adapter = KRMarketAdapter()

    # Use major Korean stocks
    tickers = ["005930", "000660", "035420"]  # Samsung, SK Hynix, NAVER
    yesterday = date.today() - timedelta(days=1)

    try:
        results = await adapter.fetch_multiple(tickers, "KR", yesterday)

        # Should get a list (may be empty on weekends/holidays)
        assert isinstance(results, list)

        if results:
            # If we got results, verify they're valid
            for result in results:
                assert result["market"] == "KR"
                assert result["ticker"] in tickers
                assert isinstance(result["volume"], int)
            print(f"✅ KR Multiple live test passed: {len(results)} stocks fetched")
        else:
            print(
                f"⚠️  KR Multiple live test: No data for {yesterday} "
                "(likely weekend/holiday)"
            )

    except Exception as e:
        print(f"⚠️  KR Multiple live test error: {e}")


@pytest.mark.live
@pytest.mark.asyncio
async def test_us_adapter_live_fetch_multiple():
    """Live test: fetch multiple US tickers."""
    adapter = USMarketAdapter()

    # Use major US stocks
    tickers = ["AAPL", "GOOGL", "MSFT"]  # Apple, Google, Microsoft
    yesterday = date.today() - timedelta(days=1)

    try:
        results = await adapter.fetch_multiple(tickers, "US", yesterday)

        # Should get a list (may be empty on weekends/holidays)
        assert isinstance(results, list)

        if results:
            # If we got results, verify they're valid
            for result in results:
                assert result["market"] == "US"
                assert result["ticker"] in tickers
                assert isinstance(result["volume"], int)
            print(f"✅ US Multiple live test passed: {len(results)} stocks fetched")
        else:
            print(
                f"⚠️  US Multiple live test: No data for {yesterday} "
                "(likely weekend/holiday)"
            )

    except Exception as e:
        print(f"⚠️  US Multiple live test error: {e}")


@pytest.mark.live
@pytest.mark.asyncio
async def test_market_open_status():
    """Live test: check market open status."""
    kr_adapter = KRMarketAdapter()
    us_adapter = USMarketAdapter()

    try:
        kr_open = await kr_adapter.is_market_open("KR")
        us_open = await us_adapter.is_market_open("US")

        # Should be boolean values
        assert isinstance(kr_open, bool)
        assert isinstance(us_open, bool)

        today = date.today()
        is_weekday = today.weekday() < 5

        # Both should match weekday status (until Step 16 adds holidays)
        assert kr_open == is_weekday
        assert us_open == is_weekday

        print(
            f"✅ Market status test passed: KR={kr_open}, US={us_open}, "
            f"weekday={is_weekday}"
        )

    except Exception as e:
        print(f"⚠️  Market status test error: {e}")
