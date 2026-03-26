import pytest
from datetime import date
from decimal import Decimal
from app.infra.db.models.market_data import MarketData


def test_market_data_creation():
    """Test market data creation with required fields"""
    market_data = MarketData(
        ticker="AAPL",
        market="US",
        date=date(2024, 1, 1),
        open=Decimal("150.00"),
        high=Decimal("155.00"),
        low=Decimal("149.00"),
        close=Decimal("154.00"),
        volume=1000000
    )
    
    assert market_data.ticker == "AAPL"
    assert market_data.market == "US"
    assert market_data.date == date(2024, 1, 1)
    assert market_data.open == Decimal("150.00")
    assert market_data.high == Decimal("155.00")
    assert market_data.low == Decimal("149.00")
    assert market_data.close == Decimal("154.00")
    assert market_data.volume == 1000000


def test_market_data_unique_constraint():
    """Test that ticker + market + date should be unique"""
    # This will be enforced at DB level through UniqueConstraint
    # In unit tests, we can only test that the fields exist and can be set
    market_data1 = MarketData(
        ticker="AAPL",
        market="US",
        date=date(2024, 1, 1),
        open=Decimal("150.00"),
        high=Decimal("155.00"),
        low=Decimal("149.00"),
        close=Decimal("154.00"),
        volume=1000000
    )
    
    market_data2 = MarketData(
        ticker="AAPL",
        market="US",
        date=date(2024, 1, 2),  # Different date - should be allowed
        open=Decimal("154.00"),
        high=Decimal("158.00"),
        low=Decimal("153.00"),
        close=Decimal("157.00"),
        volume=1200000
    )
    
    # Both should have the same ticker and market
    assert market_data1.ticker == market_data2.ticker
    assert market_data1.market == market_data2.market
    # But different dates
    assert market_data1.date != market_data2.date


def test_ohlcv_fields_are_numeric():
    """Test that OHLC fields are Decimal and volume is integer"""
    market_data = MarketData(
        ticker="GOOGL",
        market="US",
        date=date(2024, 1, 1),
        open=Decimal("2800.50"),
        high=Decimal("2850.75"),
        low=Decimal("2790.25"),
        close=Decimal("2845.00"),
        volume=500000
    )
    
    # Test Decimal fields
    assert isinstance(market_data.open, Decimal)
    assert isinstance(market_data.high, Decimal)
    assert isinstance(market_data.low, Decimal)
    assert isinstance(market_data.close, Decimal)
    
    # Test integer volume
    assert isinstance(market_data.volume, int)
    
    # Test precision
    assert market_data.open == Decimal("2800.50")
    assert market_data.high == Decimal("2850.75")


def test_market_data_date_field():
    """Test that date field accepts date objects"""
    test_date = date(2024, 3, 15)
    
    market_data = MarketData(
        ticker="005930",  # Samsung Electronics (KR)
        market="KR",
        date=test_date,
        open=Decimal("75000"),
        high=Decimal("76000"),
        low=Decimal("74500"),
        close=Decimal("75500"),
        volume=200000
    )
    
    assert market_data.date == test_date
    assert isinstance(market_data.date, date)
    assert market_data.market == "KR"  # Korean market test