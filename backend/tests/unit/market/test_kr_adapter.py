"""
Unit tests for KRMarketAdapter.
Tests are mocked to avoid real network calls.
Written in TDD Red phase - these will fail initially.
"""

from datetime import date
from unittest.mock import patch

import pandas as pd
import pytest
from app.domain.market import MarketDataFetchError, MarketDataPort


def test_kr_adapter_implements_market_data_port():
    """KRMarketAdapter implements MarketDataPort interface."""
    from app.infra.market.kr_adapter import KRMarketAdapter

    adapter = KRMarketAdapter()
    assert isinstance(adapter, MarketDataPort)


@pytest.mark.asyncio
async def test_fetch_daily_ohlcv_returns_correct_format():
    """KRMarketAdapter.fetch_daily_ohlcv returns correct dict format."""
    from app.infra.market.kr_adapter import KRMarketAdapter

    # Mock pykrx response
    mock_df = pd.DataFrame({
        '시가': [70000],
        '고가': [72000],
        '저가': [69000],
        '종가': [71000],
        '거래량': [1000000]
    })
    mock_df.index = pd.to_datetime(['2024-01-02'])

    adapter = KRMarketAdapter()

    with patch('pykrx.stock.get_market_ohlcv_by_date') as mock_get_data:
        mock_get_data.return_value = mock_df

        result = await adapter.fetch_daily_ohlcv("005930", "KR", date(2024, 1, 2))

    assert result is not None
    assert result["ticker"] == "005930"
    assert result["market"] == "KR"
    assert result["date"] == "2024-01-02"
    assert result["open"] == 70000.0
    assert result["high"] == 72000.0
    assert result["low"] == 69000.0
    assert result["close"] == 71000.0
    assert result["volume"] == 1000000


@pytest.mark.asyncio
async def test_fetch_daily_ohlcv_returns_none_for_holiday():
    """KRMarketAdapter returns None when no data (holiday/weekend)."""
    from app.infra.market.kr_adapter import KRMarketAdapter

    # Mock empty DataFrame (no trading data)
    empty_df = pd.DataFrame()

    adapter = KRMarketAdapter()

    with patch('pykrx.stock.get_market_ohlcv_by_date') as mock_get_data:
        mock_get_data.return_value = empty_df

        result = await adapter.fetch_daily_ohlcv("005930", "KR", date(2024, 1, 1))

    assert result is None


@pytest.mark.asyncio
async def test_fetch_daily_ohlcv_raises_on_network_error():
    """KRMarketAdapter raises MarketDataFetchError on network failure."""
    from app.infra.market.kr_adapter import KRMarketAdapter

    adapter = KRMarketAdapter()

    with patch('pykrx.stock.get_market_ohlcv_by_date') as mock_get_data:
        mock_get_data.side_effect = ConnectionError("Network error")

        with pytest.raises(MarketDataFetchError) as exc_info:
            await adapter.fetch_daily_ohlcv("005930", "KR", date(2024, 1, 2))

        assert "005930" in str(exc_info.value)
        assert "KR" in str(exc_info.value)
        assert "Network error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fetch_multiple_returns_list():
    """KRMarketAdapter.fetch_multiple returns list of dicts for multiple tickers."""
    from app.infra.market.kr_adapter import KRMarketAdapter

    # Mock successful response for all tickers
    mock_df = pd.DataFrame({
        '시가': [70000],
        '고가': [72000],
        '저가': [69000],
        '종가': [71000],
        '거래량': [1000000]
    })
    mock_df.index = pd.to_datetime(['2024-01-02'])

    adapter = KRMarketAdapter()

    with patch('pykrx.stock.get_market_ohlcv_by_date') as mock_get_data:
        mock_get_data.return_value = mock_df

        result = await adapter.fetch_multiple(
            ["005930", "000660", "035420"], "KR", date(2024, 1, 2)
        )

    assert isinstance(result, list)
    assert len(result) == 3
    assert all(isinstance(item, dict) for item in result)
    assert result[0]["ticker"] == "005930"
    assert result[1]["ticker"] == "000660"
    assert result[2]["ticker"] == "035420"


@pytest.mark.asyncio
async def test_fetch_multiple_skips_failed_tickers():
    """KRMarketAdapter.fetch_multiple skips failed tickers, doesn't crash."""
    from app.infra.market.kr_adapter import KRMarketAdapter

    # Mock responses: success, empty, success
    success_df = pd.DataFrame({
        '시가': [70000],
        '고가': [72000],
        '저가': [69000],
        '종가': [71000],
        '거래량': [1000000]
    })
    success_df.index = pd.to_datetime(['2024-01-02'])

    empty_df = pd.DataFrame()

    adapter = KRMarketAdapter()

    def mock_side_effect(start_date, end_date, ticker):
        if ticker == "000660":  # middle ticker fails
            return empty_df
        return success_df

    with patch('pykrx.stock.get_market_ohlcv_by_date', side_effect=mock_side_effect):
        result = await adapter.fetch_multiple(
            ["005930", "000660", "035420"], "KR", date(2024, 1, 2)
        )

    # Should return 2 items (skip the empty one)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["ticker"] == "005930"
    assert result[1]["ticker"] == "035420"


@pytest.mark.asyncio
async def test_is_market_open_weekday():
    """KRMarketAdapter.is_market_open returns True for weekdays."""
    from app.infra.market.kr_adapter import KRMarketAdapter

    adapter = KRMarketAdapter()

    # Mock a Monday
    with patch('app.infra.market.kr_adapter.date') as mock_date:
        mock_date.today.return_value = date(2024, 1, 1)  # Monday

        result = await adapter.is_market_open("KR")

    assert result is True


@pytest.mark.asyncio
async def test_is_market_open_weekend():
    """KRMarketAdapter.is_market_open returns False for weekends."""
    from app.infra.market.kr_adapter import KRMarketAdapter

    adapter = KRMarketAdapter()

    # Mock a Saturday
    with patch('app.infra.market.kr_adapter.date') as mock_date:
        mock_date.today.return_value = date(2024, 1, 6)  # Saturday

        result = await adapter.is_market_open("KR")

    assert result is False
