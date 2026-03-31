import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def kr_mock_ohlcv():
    """Standard KR market OHLCV data fixture."""
    return {
        "ticker": "005930",
        "market": "KR",
        "date": date.today().isoformat(),
        "open": 71000.0,
        "high": 72000.0,
        "low": 70500.0,
        "close": 71500.0,
        "volume": 15000000,
    }


@pytest.fixture
def us_mock_ohlcv():
    """Standard US market OHLCV data fixture."""
    return {
        "ticker": "AAPL",
        "market": "US",
        "date": (date.today() - timedelta(days=1)).isoformat(),
        "open": 180.00,
        "high": 182.50,
        "low": 179.50,
        "close": 181.00,
        "volume": 52000000,
    }


@pytest.fixture
def mock_kr_adapter(kr_mock_ohlcv):
    """Mock KR adapter returning valid data."""
    adapter = AsyncMock()
    adapter.fetch_daily_ohlcv.return_value = kr_mock_ohlcv
    adapter.fetch_multiple.return_value = [kr_mock_ohlcv]
    adapter.is_market_open.return_value = True
    return adapter


@pytest.fixture
def mock_us_adapter(us_mock_ohlcv):
    """Mock US adapter returning valid data."""
    adapter = AsyncMock()
    adapter.fetch_daily_ohlcv.return_value = us_mock_ohlcv
    adapter.fetch_multiple.return_value = [us_mock_ohlcv]
    adapter.is_market_open.return_value = True
    return adapter


@pytest.fixture
def failing_kr_adapter():
    """Mock KR adapter that always fails."""
    from app.domain.market.exceptions import MarketDataFetchError
    
    adapter = AsyncMock()
    adapter.fetch_daily_ohlcv.side_effect = MarketDataFetchError(
        "005930", "KR", "Simulated KR failure"
    )
    adapter.fetch_multiple.side_effect = MarketDataFetchError(
        "005930", "KR", "Simulated KR failure"
    )
    return adapter


@pytest.fixture
def failing_us_adapter():
    """Mock US adapter that always fails."""
    from app.domain.market.exceptions import MarketDataFetchError
    
    adapter = AsyncMock()
    adapter.fetch_daily_ohlcv.side_effect = MarketDataFetchError(
        "AAPL", "US", "Simulated US failure"
    )
    return adapter


@pytest.fixture
def mock_ai_output():
    """Standard AI output fixture."""
    from app.domain.ai.schemas import AIPromptOutput, StockStrategy, TakeProfitLevel, StopLossLevel
    
    return AIPromptOutput(
        market_summary="테스트 시장 분석 요약",
        strategies=[
            StockStrategy(
                ticker="005930",
                action="hold",
                take_profit=[TakeProfitLevel(pct=10.0, sell_ratio=0.3)],
                stop_loss=[StopLossLevel(pct=-5.0, sell_ratio=0.5)],
                rationale="테스트 전략 근거",
                confidence=0.75,
            )
        ]
    )