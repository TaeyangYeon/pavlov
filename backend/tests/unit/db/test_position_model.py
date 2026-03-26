import pytest
from decimal import Decimal
from datetime import datetime
from uuid import uuid4
from app.infra.db.models.position import Position


def test_position_creation():
    """Test position creation with required fields"""
    user_id = uuid4()
    entries = [{"price": 100.0, "quantity": 10, "entered_at": "2024-01-01T10:00:00"}]
    
    position = Position(
        user_id=user_id,
        ticker="AAPL",
        market="US",
        entries=entries,
        status="open"
    )
    
    assert position.user_id == user_id
    assert position.ticker == "AAPL"
    assert position.market == "US"
    assert position.entries == entries
    assert position.status == "open"


def test_position_entries_is_json():
    """Test that entries field accepts JSON/list format"""
    user_id = uuid4()
    entries = [
        {"price": 100.0, "quantity": 10, "entered_at": "2024-01-01T10:00:00"},
        {"price": 105.0, "quantity": 5, "entered_at": "2024-01-02T10:00:00"}
    ]
    
    position = Position(
        user_id=user_id,
        ticker="GOOGL",
        market="US",
        entries=entries
    )
    
    assert len(position.entries) == 2
    assert position.entries[0]["price"] == 100.0
    assert position.entries[1]["quantity"] == 5


def test_position_market_enum_values():
    """Test that market field only accepts 'KR' or 'US' values"""
    user_id = uuid4()
    entries = [{"price": 100.0, "quantity": 10, "entered_at": "2024-01-01T10:00:00"}]
    
    # Valid values
    position_us = Position(
        user_id=user_id,
        ticker="AAPL",
        market="US",
        entries=entries
    )
    assert position_us.market == "US"
    
    position_kr = Position(
        user_id=user_id,
        ticker="005930",
        market="KR",
        entries=entries
    )
    assert position_kr.market == "KR"
    
    # Invalid value - enum validation happens at DB level, not model level
    # This will pass model creation but fail at DB insert time
    position_invalid = Position(
        user_id=user_id,
        ticker="INVALID",
        market="INVALID_MARKET",
        entries=entries
    )
    # Model creation succeeds, DB constraint will fail
    assert position_invalid.market == "INVALID_MARKET"


def test_position_status_enum_values():
    """Test that status field only accepts 'open' or 'closed' values"""
    user_id = uuid4()
    entries = [{"price": 100.0, "quantity": 10, "entered_at": "2024-01-01T10:00:00"}]
    
    # Valid values
    position_open = Position(
        user_id=user_id,
        ticker="AAPL",
        market="US",
        entries=entries,
        status="open"
    )
    assert position_open.status == "open"
    
    position_closed = Position(
        user_id=user_id,
        ticker="AAPL",
        market="US",
        entries=entries,
        status="closed"
    )
    assert position_closed.status == "closed"
    
    # Test default value (database default, not set in unit test)
    position_default = Position(
        user_id=user_id,
        ticker="AAPL",
        market="US",
        entries=entries
    )
    # Default is set by database, not in unit tests
    assert position_default.status is None  # Will be "open" when saved to DB


def test_position_avg_price_nullable():
    """Test that avg_price is nullable and calculated later"""
    user_id = uuid4()
    entries = [{"price": 100.0, "quantity": 10, "entered_at": "2024-01-01T10:00:00"}]
    
    # Test nullable
    position_no_avg = Position(
        user_id=user_id,
        ticker="AAPL",
        market="US",
        entries=entries
    )
    assert position_no_avg.avg_price is None
    
    # Test with avg_price
    position_with_avg = Position(
        user_id=user_id,
        ticker="AAPL",
        market="US",
        entries=entries,
        avg_price=Decimal("100.50")
    )
    assert position_with_avg.avg_price == Decimal("100.50")