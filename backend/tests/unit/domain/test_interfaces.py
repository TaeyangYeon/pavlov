"""
Test contracts for all domain interfaces.
Tests verify ABC pattern and interface compliance.
Written in TDD Red phase - these will fail initially.
"""

from datetime import date
from uuid import UUID, uuid4

import pytest
from app.domain.position.schemas import PositionCreate, PositionResponse


def test_market_data_port_is_abstract():
    """MarketDataPort cannot be instantiated directly."""
    from app.domain.market.interfaces import MarketDataPort

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        MarketDataPort()


def test_position_repository_port_is_abstract():
    """PositionRepositoryPort cannot be instantiated directly."""
    from app.domain.position.interfaces import PositionRepositoryPort

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        PositionRepositoryPort()


def test_filter_port_is_abstract():
    """FilterPort cannot be instantiated directly."""
    from app.domain.filter.interfaces import FilterPort

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        FilterPort()


def test_indicator_port_is_abstract():
    """IndicatorPort cannot be instantiated directly."""
    from app.domain.indicator.interfaces import IndicatorPort

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IndicatorPort()


def test_strategy_port_is_abstract():
    """StrategyPort cannot be instantiated directly."""
    from app.domain.strategy.interfaces import StrategyPort

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        StrategyPort()


def test_mock_market_data_port_implements_interface():
    """Mock implementation satisfies MarketDataPort ABC contract."""
    from app.domain.market.interfaces import MarketDataPort

    class MockMarketDataPort(MarketDataPort):
        async def fetch_daily_ohlcv(
            self, ticker: str, market: str, date: date
        ) -> dict | None:
            return {"ticker": ticker, "market": market, "date": str(date)}

        async def fetch_multiple(
            self, tickers: list[str], market: str, date: date
        ) -> list[dict]:
            return [{"ticker": t, "market": market} for t in tickers]

        async def is_market_open(self, market: str) -> bool:
            return True

    # Should instantiate without error
    mock = MockMarketDataPort()
    assert isinstance(mock, MarketDataPort)
    assert hasattr(mock, 'fetch_daily_ohlcv')
    assert hasattr(mock, 'fetch_multiple')
    assert hasattr(mock, 'is_market_open')


def test_mock_position_repository_implements_interface():
    """Mock implementation satisfies PositionRepositoryPort ABC contract."""
    from app.domain.position.interfaces import PositionRepositoryPort

    class MockPositionRepository(PositionRepositoryPort):
        async def create(self, data: PositionCreate, user_id: UUID) -> PositionResponse:
            return PositionResponse(
                id=uuid4(),
                user_id=user_id,
                ticker=data.ticker,
                market=data.market,
                position_type=data.position_type,
                shares=data.shares,
                entry_price=data.entry_price,
                is_open=True,
                created_at=date.today(),
                updated_at=date.today(),
            )

        async def get_by_id(self, position_id: UUID) -> PositionResponse | None:
            return None

        async def get_by_user(self, user_id: UUID) -> list[PositionResponse]:
            return []

        async def get_open_positions(self, user_id: UUID) -> list[PositionResponse]:
            return []

        async def update(
            self, position_id: UUID, data: dict
        ) -> PositionResponse | None:
            return None

        async def delete(self, position_id: UUID) -> bool:
            return True

    # Should instantiate without error
    mock = MockPositionRepository()
    assert isinstance(mock, PositionRepositoryPort)
    assert hasattr(mock, 'create')
    assert hasattr(mock, 'get_by_id')
    assert hasattr(mock, 'get_by_user')
    assert hasattr(mock, 'get_open_positions')
    assert hasattr(mock, 'update')
    assert hasattr(mock, 'delete')
