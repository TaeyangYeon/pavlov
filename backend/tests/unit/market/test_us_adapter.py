"""
Unit tests for USMarketAdapter.
Tests are mocked to avoid real network calls.
Written in TDD Red phase - these will fail initially.
"""

from datetime import date
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from app.domain.market import MarketDataFetchError, MarketDataPort


def test_us_adapter_implements_market_data_port():
    """USMarketAdapter implements MarketDataPort interface."""
    from app.infra.market.us_adapter import USMarketAdapter

    adapter = USMarketAdapter()
    assert isinstance(adapter, MarketDataPort)


@pytest.mark.asyncio
async def test_fetch_daily_ohlcv_returns_correct_format():
    """USMarketAdapter.fetch_daily_ohlcv returns correct dict format."""
    from app.infra.market.us_adapter import USMarketAdapter

    # Mock yfinance response
    mock_df = pd.DataFrame(
        {
            'Open': [150.0],
            'High': [155.0],
            'Low': [148.0],
            'Close': [152.0],
            'Volume': [50000000],
        }
    )
    mock_df.index = pd.to_datetime(['2024-01-02'])

    mock_ticker = Mock()
    mock_ticker.history.return_value = mock_df

    adapter = USMarketAdapter()

    with patch('yfinance.Ticker', return_value=mock_ticker):
        result = await adapter.fetch_daily_ohlcv("AAPL", "US", date(2024, 1, 2))

    assert result is not None
    assert result["ticker"] == "AAPL"
    assert result["market"] == "US"
    assert result["date"] == "2024-01-02"
    assert result["open"] == 150.0
    assert result["high"] == 155.0
    assert result["low"] == 148.0
    assert result["close"] == 152.0
    assert result["volume"] == 50000000


@pytest.mark.asyncio
async def test_fetch_daily_ohlcv_returns_none_for_no_data():
    """USMarketAdapter returns None when no data available."""
    from app.infra.market.us_adapter import USMarketAdapter

    # Mock empty DataFrame
    empty_df = pd.DataFrame()

    mock_ticker = Mock()
    mock_ticker.history.return_value = empty_df

    adapter = USMarketAdapter()

    with patch('yfinance.Ticker', return_value=mock_ticker):
        result = await adapter.fetch_daily_ohlcv("AAPL", "US", date(2024, 1, 1))

    assert result is None


@pytest.mark.asyncio
async def test_fetch_daily_ohlcv_raises_on_network_error():
    """USMarketAdapter raises MarketDataFetchError on network failure."""
    from app.infra.market.us_adapter import USMarketAdapter

    mock_ticker = Mock()
    mock_ticker.history.side_effect = Exception("Network timeout")

    adapter = USMarketAdapter()

    with patch('yfinance.Ticker', return_value=mock_ticker):
        with pytest.raises(MarketDataFetchError) as exc_info:
            await adapter.fetch_daily_ohlcv("AAPL", "US", date(2024, 1, 2))

        assert "AAPL" in str(exc_info.value)
        assert "US" in str(exc_info.value)
        assert "Network timeout" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fetch_multiple_returns_list():
    """USMarketAdapter.fetch_multiple returns list of dicts for multiple tickers."""
    from app.infra.market.us_adapter import USMarketAdapter

    # Mock successful response
    mock_df = pd.DataFrame(
        {
            'Open': [150.0],
            'High': [155.0],
            'Low': [148.0],
            'Close': [152.0],
            'Volume': [50000000],
        }
    )
    mock_df.index = pd.to_datetime(['2024-01-02'])

    mock_ticker = Mock()
    mock_ticker.history.return_value = mock_df

    adapter = USMarketAdapter()

    with patch('yfinance.Ticker', return_value=mock_ticker):
        result = await adapter.fetch_multiple(
            ["AAPL", "GOOGL", "MSFT"], "US", date(2024, 1, 2)
        )

    assert isinstance(result, list)
    assert len(result) == 3
    assert all(isinstance(item, dict) for item in result)
    assert result[0]["ticker"] == "AAPL"
    assert result[1]["ticker"] == "GOOGL"
    assert result[2]["ticker"] == "MSFT"


@pytest.mark.asyncio
async def test_fetch_multiple_skips_failed_tickers():
    """USMarketAdapter.fetch_multiple skips failed tickers, doesn't crash."""
    from app.infra.market.us_adapter import USMarketAdapter

    # Mock responses: success, empty, success
    success_df = pd.DataFrame(
        {
            'Open': [150.0],
            'High': [155.0],
            'Low': [148.0],
            'Close': [152.0],
            'Volume': [50000000],
        }
    )
    success_df.index = pd.to_datetime(['2024-01-02'])

    empty_df = pd.DataFrame()

    def mock_ticker_factory(symbol):
        mock_ticker = Mock()
        if symbol == "GOOGL":  # middle ticker fails
            mock_ticker.history.return_value = empty_df
        else:
            mock_ticker.history.return_value = success_df
        return mock_ticker

    adapter = USMarketAdapter()

    with patch('yfinance.Ticker', side_effect=mock_ticker_factory):
        result = await adapter.fetch_multiple(
            ["AAPL", "GOOGL", "MSFT"], "US", date(2024, 1, 2)
        )

    # Should return 2 items (skip the empty one)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["ticker"] == "AAPL"
    assert result[1]["ticker"] == "MSFT"


@pytest.mark.asyncio
async def test_is_market_open_weekday():
    """USMarketAdapter.is_market_open returns True for weekdays."""
    from app.infra.market.us_adapter import USMarketAdapter

    adapter = USMarketAdapter()

    # Mock a Monday
    with patch('app.infra.market.us_adapter.date') as mock_date:
        mock_date.today.return_value = date(2024, 1, 1)  # Monday

        result = await adapter.is_market_open("US")

    assert result is True


@pytest.mark.asyncio
async def test_is_market_open_weekend():
    """USMarketAdapter.is_market_open returns False for weekends."""
    from app.infra.market.us_adapter import USMarketAdapter

    adapter = USMarketAdapter()

    # Mock a Sunday
    with patch('app.infra.market.us_adapter.date') as mock_date:
        mock_date.today.return_value = date(2024, 1, 7)  # Sunday

        result = await adapter.is_market_open("US")

    assert result is False


@pytest.mark.asyncio
async def test_us_ticker_format_uppercase():
    """USMarketAdapter normalizes ticker to uppercase."""
    from app.infra.market.us_adapter import USMarketAdapter

    # Mock yfinance response
    mock_df = pd.DataFrame(
        {
            'Open': [150.0],
            'High': [155.0],
            'Low': [148.0],
            'Close': [152.0],
            'Volume': [50000000],
        }
    )
    mock_df.index = pd.to_datetime(['2024-01-02'])

    mock_ticker = Mock()
    mock_ticker.history.return_value = mock_df

    adapter = USMarketAdapter()

    with patch('yfinance.Ticker', return_value=mock_ticker) as mock_yfinance:
        result = await adapter.fetch_daily_ohlcv("aapl", "US", date(2024, 1, 2))

        # Verify uppercase normalization
        mock_yfinance.assert_called_once_with("AAPL")
        assert result["ticker"] == "AAPL"
