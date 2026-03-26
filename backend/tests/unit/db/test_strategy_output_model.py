import pytest
from decimal import Decimal
from uuid import uuid4
from app.infra.db.models.strategy_output import StrategyOutput


def test_strategy_output_creation():
    """Test strategy output creation with required fields"""
    analysis_log_id = uuid4()
    take_profit_levels = [
        {"pct": 5.0, "sell_ratio": 0.5},
        {"pct": 10.0, "sell_ratio": 0.5}
    ]
    stop_loss_levels = [
        {"pct": -3.0, "sell_ratio": 1.0}
    ]
    
    strategy_output = StrategyOutput(
        analysis_log_id=analysis_log_id,
        ticker="AAPL",
        action="buy",
        take_profit_levels=take_profit_levels,
        stop_loss_levels=stop_loss_levels,
        rationale="Strong momentum indicators",
        confidence=Decimal("0.85")
    )
    
    assert strategy_output.analysis_log_id == analysis_log_id
    assert strategy_output.ticker == "AAPL"
    assert strategy_output.action == "buy"
    assert strategy_output.rationale == "Strong momentum indicators"
    assert strategy_output.confidence == Decimal("0.85")


def test_tp_levels_stored_as_json():
    """Test that take_profit_levels are stored as JSON"""
    analysis_log_id = uuid4()
    take_profit_levels = [
        {"pct": 5.0, "sell_ratio": 0.3},
        {"pct": 10.0, "sell_ratio": 0.4},
        {"pct": 15.0, "sell_ratio": 0.3}
    ]
    
    strategy_output = StrategyOutput(
        analysis_log_id=analysis_log_id,
        ticker="GOOGL",
        action="buy",
        take_profit_levels=take_profit_levels,
        stop_loss_levels=[],
        rationale="Multiple TP levels test",
        confidence=Decimal("0.75")
    )
    
    assert len(strategy_output.take_profit_levels) == 3
    assert strategy_output.take_profit_levels[0]["pct"] == 5.0
    assert strategy_output.take_profit_levels[0]["sell_ratio"] == 0.3
    assert strategy_output.take_profit_levels[2]["pct"] == 15.0


def test_sl_levels_stored_as_json():
    """Test that stop_loss_levels are stored as JSON"""
    analysis_log_id = uuid4()
    stop_loss_levels = [
        {"pct": -5.0, "sell_ratio": 0.5},
        {"pct": -10.0, "sell_ratio": 0.5}
    ]
    
    strategy_output = StrategyOutput(
        analysis_log_id=analysis_log_id,
        ticker="TSLA",
        action="partial_sell",
        take_profit_levels=[],
        stop_loss_levels=stop_loss_levels,
        rationale="Risk management with multiple SL levels",
        confidence=Decimal("0.60")
    )
    
    assert len(strategy_output.stop_loss_levels) == 2
    assert strategy_output.stop_loss_levels[0]["pct"] == -5.0
    assert strategy_output.stop_loss_levels[1]["sell_ratio"] == 0.5


def test_foreign_key_to_analysis_log():
    """Test that analysis_log_id foreign key relationship works"""
    analysis_log_id = uuid4()
    
    strategy_output = StrategyOutput(
        analysis_log_id=analysis_log_id,
        ticker="MSFT",
        action="hold",
        take_profit_levels=[],
        stop_loss_levels=[{"pct": -3.0, "sell_ratio": 1.0}],
        rationale="Hold current position",
        confidence=Decimal("0.70")
    )
    
    # Test that the foreign key is set correctly
    assert strategy_output.analysis_log_id == analysis_log_id
    # Actual foreign key constraint will be tested in integration tests


def test_action_enum_values():
    """Test that action field accepts valid enum values"""
    analysis_log_id = uuid4()
    
    # Test all valid actions
    valid_actions = ["hold", "buy", "partial_sell", "full_exit"]
    
    for action in valid_actions:
        strategy_output = StrategyOutput(
            analysis_log_id=analysis_log_id,
            ticker="TEST",
            action=action,
            take_profit_levels=[],
            stop_loss_levels=[],
            rationale=f"Testing {action} action",
            confidence=Decimal("0.80")
        )
        assert strategy_output.action == action
    
    # Invalid action - enum validation happens at DB level, not model level
    strategy_invalid = StrategyOutput(
        analysis_log_id=analysis_log_id,
        ticker="TEST",
        action="invalid_action",
        take_profit_levels=[],
        stop_loss_levels=[],
        rationale="This should pass model creation",
        confidence=Decimal("0.80")
    )
    # Model creation succeeds, DB constraint will fail
    assert strategy_invalid.action == "invalid_action"