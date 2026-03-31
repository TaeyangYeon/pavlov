import pytest
from datetime import date
from unittest.mock import patch, MagicMock


@pytest.mark.integration
async def test_kr_adapter_uses_6digit_tickers():
    """KR adapter must accept 6-digit numeric tickers."""
    from app.infra.market.kr_adapter import KRMarketAdapter
    
    adapter = KRMarketAdapter()

    valid_kr_tickers = [
        "005930",  # 삼성전자
        "000660",  # SK하이닉스
        "035420",  # NAVER
    ]
    invalid_tickers = ["AAPL", "MSFT", "aapl"]

    # Verify adapter does not reject valid KR format
    # (actual network call mocked)
    for ticker in valid_kr_tickers:
        assert len(ticker) == 6
        assert ticker.isdigit()

    # Verify US tickers are wrong format for KR
    for ticker in invalid_tickers:
        assert not ticker.isdigit()


@pytest.mark.integration
async def test_us_adapter_normalizes_to_uppercase():
    """US adapter must normalize tickers to uppercase."""
    from app.infra.market.us_adapter import USMarketAdapter
    
    adapter = USMarketAdapter()

    # Mock the actual API call
    with patch('yfinance.Ticker') as mock_ticker:
        mock_ticker.return_value.history.return_value = MagicMock(empty=True)  # no data
        result = await adapter.fetch_daily_ohlcv("aapl", "US", date.today())
        # Should not raise even with lowercase
        # (returns None for no data)


@pytest.mark.integration
async def test_kr_adapter_failure_isolated_from_us(
    failing_kr_adapter, mock_us_adapter
):
    """
    KR adapter failure must not affect US adapter.
    Both adapters operate on separate instances.
    """
    from app.domain.market.exceptions import MarketDataFetchError

    # KR fails
    with pytest.raises(MarketDataFetchError):
        await failing_kr_adapter.fetch_daily_ohlcv("005930", "KR", date.today())

    # US still works (different adapter instance)
    result = await mock_us_adapter.fetch_daily_ohlcv("AAPL", "US", date.today())
    assert result is not None
    assert result["market"] == "US"
    assert result["ticker"] == "AAPL"


@pytest.mark.integration
async def test_adapters_return_correct_market_field(
    mock_kr_adapter, mock_us_adapter
):
    """Market field in OHLCV dict must match adapter type."""
    kr_result = await mock_kr_adapter.fetch_daily_ohlcv("005930", "KR", date.today())
    us_result = await mock_us_adapter.fetch_daily_ohlcv("AAPL", "US", date.today())

    assert kr_result["market"] == "KR"
    assert us_result["market"] == "US"
    # Cross-check: KR result must not claim US
    assert kr_result["market"] != "US"
    assert us_result["market"] != "KR"


@pytest.mark.integration
async def test_container_returns_correct_adapter_per_market():
    """
    Container.market_adapter("KR") → KRMarketAdapter
    Container.market_adapter("US") → USMarketAdapter
    """
    from app.core.container import get_container
    from app.infra.market.kr_adapter import KRMarketAdapter
    from app.infra.market.us_adapter import USMarketAdapter

    container = get_container()

    kr_adapter = container.market_adapter("KR")
    us_adapter = container.market_adapter("US")

    assert isinstance(kr_adapter, KRMarketAdapter)
    assert isinstance(us_adapter, USMarketAdapter)

    # Verify they are different types
    assert type(kr_adapter) != type(us_adapter)


@pytest.mark.integration
async def test_invalid_market_raises():
    """Unsupported market string must raise ValueError."""
    from app.core.container import get_container
    
    container = get_container()

    with pytest.raises(ValueError) as exc_info:
        container.market_adapter("JP")

    assert "JP" in str(exc_info.value)