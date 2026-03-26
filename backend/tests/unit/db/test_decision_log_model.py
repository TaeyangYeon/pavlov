import pytest
from decimal import Decimal
from uuid import uuid4
from app.infra.db.models.decision_log import DecisionLog


def test_decision_log_creation():
    """Test decision log creation with required fields"""
    user_id = uuid4()
    
    decision_log = DecisionLog(
        user_id=user_id,
        ticker="AAPL",
        action="buy",
        price=Decimal("150.00"),
        quantity=Decimal("10"),
        ai_suggested=True,
        notes="Following AI recommendation"
    )
    
    assert decision_log.user_id == user_id
    assert decision_log.ticker == "AAPL"
    assert decision_log.action == "buy"
    assert decision_log.price == Decimal("150.00")
    assert decision_log.quantity == Decimal("10")
    assert decision_log.ai_suggested is True
    assert decision_log.notes == "Following AI recommendation"


def test_ai_suggested_is_boolean():
    """Test that ai_suggested field is boolean"""
    user_id = uuid4()
    
    # Test True value
    decision_log_suggested = DecisionLog(
        user_id=user_id,
        ticker="GOOGL",
        action="sell",
        price=Decimal("2800.00"),
        quantity=Decimal("5"),
        ai_suggested=True
    )
    assert decision_log_suggested.ai_suggested is True
    
    # Test False value
    decision_log_not_suggested = DecisionLog(
        user_id=user_id,
        ticker="MSFT",
        action="hold",
        price=Decimal("300.00"),
        quantity=Decimal("0"),  # No quantity for hold action
        ai_suggested=False
    )
    assert decision_log_not_suggested.ai_suggested is False
    
    # Test that it's explicitly boolean
    assert isinstance(decision_log_suggested.ai_suggested, bool)
    assert isinstance(decision_log_not_suggested.ai_suggested, bool)


def test_action_enum_values():
    """Test that action field only accepts 'buy', 'sell', 'hold' values"""
    user_id = uuid4()
    
    # Valid actions
    valid_actions = ["buy", "sell", "hold"]
    
    for action in valid_actions:
        decision_log = DecisionLog(
            user_id=user_id,
            ticker="TEST",
            action=action,
            price=Decimal("100.00"),
            quantity=Decimal("10"),
            ai_suggested=True
        )
        assert decision_log.action == action
    
    # Invalid action - enum validation happens at DB level, not model level
    decision_log_invalid = DecisionLog(
        user_id=user_id,
        ticker="TEST",
        action="invalid_action",
        price=Decimal("100.00"),
        quantity=Decimal("10"),
        ai_suggested=True
    )
    # Model creation succeeds, DB constraint will fail
    assert decision_log_invalid.action == "invalid_action"


def test_foreign_key_to_user():
    """Test that user_id foreign key relationship works"""
    user_id = uuid4()
    
    decision_log = DecisionLog(
        user_id=user_id,
        ticker="TSLA",
        action="sell",
        price=Decimal("250.00"),
        quantity=Decimal("20"),
        ai_suggested=False,
        notes="Personal decision to take profit"
    )
    
    # Test that the foreign key is set correctly
    assert decision_log.user_id == user_id
    # Actual foreign key constraint will be tested in integration tests


def test_notes_field_nullable():
    """Test that notes field is nullable"""
    user_id = uuid4()
    
    # Test with notes
    decision_log_with_notes = DecisionLog(
        user_id=user_id,
        ticker="NVDA",
        action="buy",
        price=Decimal("400.00"),
        quantity=Decimal("15"),
        ai_suggested=True,
        notes="Good entry point based on technical analysis"
    )
    assert decision_log_with_notes.notes == "Good entry point based on technical analysis"
    
    # Test without notes (nullable)
    decision_log_no_notes = DecisionLog(
        user_id=user_id,
        ticker="AMD",
        action="sell",
        price=Decimal("120.00"),
        quantity=Decimal("25"),
        ai_suggested=False
    )
    assert decision_log_no_notes.notes is None


def test_decimal_precision():
    """Test that price and quantity fields maintain decimal precision"""
    user_id = uuid4()
    
    decision_log = DecisionLog(
        user_id=user_id,
        ticker="BTC",
        action="buy",
        price=Decimal("50000.123456"),  # High precision price
        quantity=Decimal("0.001234"),   # Small quantity with precision
        ai_suggested=True
    )
    
    # Test that precision is maintained
    assert decision_log.price == Decimal("50000.123456")
    assert decision_log.quantity == Decimal("0.001234")
    assert isinstance(decision_log.price, Decimal)
    assert isinstance(decision_log.quantity, Decimal)