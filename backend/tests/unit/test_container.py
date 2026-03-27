"""
Test dependency injection container.
"""

import pytest
from app.core.config import Settings
from app.core.container import Container, get_container
from app.domain.market import MarketDataPort
from app.infra.market.kr_adapter import KRMarketAdapter
from app.infra.market.us_adapter import USMarketAdapter


def test_container_kr_market_adapter():
    """Container creates KRMarketAdapter correctly."""
    settings = Settings(
        SECRET_KEY="test",
        DATABASE_URL="postgresql://test",
        POSTGRES_USER="test",
        POSTGRES_PASSWORD="test",
        POSTGRES_DB="test"
    )
    container = Container(settings)

    adapter = container.kr_market_adapter()

    assert isinstance(adapter, MarketDataPort)
    assert isinstance(adapter, KRMarketAdapter)


def test_container_us_market_adapter():
    """Container creates USMarketAdapter correctly."""
    settings = Settings(
        SECRET_KEY="test",
        DATABASE_URL="postgresql://test",
        POSTGRES_USER="test",
        POSTGRES_PASSWORD="test",
        POSTGRES_DB="test"
    )
    container = Container(settings)

    adapter = container.us_market_adapter()

    assert isinstance(adapter, MarketDataPort)
    assert isinstance(adapter, USMarketAdapter)


def test_container_market_adapter_kr():
    """Container.market_adapter returns KRMarketAdapter for 'KR'."""
    settings = Settings(
        SECRET_KEY="test",
        DATABASE_URL="postgresql://test",
        POSTGRES_USER="test",
        POSTGRES_PASSWORD="test",
        POSTGRES_DB="test"
    )
    container = Container(settings)

    adapter = container.market_adapter("KR")

    assert isinstance(adapter, MarketDataPort)
    assert isinstance(adapter, KRMarketAdapter)


def test_container_market_adapter_us():
    """Container.market_adapter returns USMarketAdapter for 'US'."""
    settings = Settings(
        SECRET_KEY="test",
        DATABASE_URL="postgresql://test",
        POSTGRES_USER="test",
        POSTGRES_PASSWORD="test",
        POSTGRES_DB="test"
    )
    container = Container(settings)

    adapter = container.market_adapter("US")

    assert isinstance(adapter, MarketDataPort)
    assert isinstance(adapter, USMarketAdapter)


def test_container_market_adapter_invalid_market():
    """Container.market_adapter raises ValueError for unsupported market."""
    settings = Settings(
        SECRET_KEY="test",
        DATABASE_URL="postgresql://test",
        POSTGRES_USER="test",
        POSTGRES_PASSWORD="test",
        POSTGRES_DB="test"
    )
    container = Container(settings)

    with pytest.raises(ValueError, match="Unsupported market: INVALID"):
        container.market_adapter("INVALID")


def test_get_container_singleton():
    """get_container() returns singleton instance."""
    container1 = get_container()
    container2 = get_container()

    assert container1 is container2
    assert isinstance(container1, Container)
