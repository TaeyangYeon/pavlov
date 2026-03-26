from app.domain.ai.schemas import (
    AIPromptOutput,
    StockStrategy,
    StopLossLevel,
    TakeProfitLevel,
    ValidationResult,
)
from app.domain.ai.validators import validate_ai_output


def test_valid_strategy_passes():
    """Test that valid strategy passes validation"""
    strategy = StockStrategy(
        ticker="AAPL",
        action="buy",
        take_profit=[
            TakeProfitLevel(pct=5.0, sell_ratio=0.5),
            TakeProfitLevel(pct=10.0, sell_ratio=0.5),
        ],
        stop_loss=[StopLossLevel(pct=-3.0, sell_ratio=1.0)],
        rationale="Strong momentum",
        confidence=0.8,
    )
    output = AIPromptOutput(market_summary="Market is bullish", strategies=[strategy])
    result = validate_ai_output(output)
    assert isinstance(result, ValidationResult)
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_low_confidence_rejected():
    """Test that low confidence (< 0.3) is rejected"""
    strategy = StockStrategy(
        ticker="AAPL",
        action="buy",
        take_profit=[TakeProfitLevel(pct=5.0, sell_ratio=1.0)],
        stop_loss=[],
        rationale="Low confidence trade",
        confidence=0.2,  # Below 0.3 threshold
    )
    output = AIPromptOutput(market_summary="Market is uncertain", strategies=[strategy])
    result = validate_ai_output(output)
    assert isinstance(result, ValidationResult)
    assert result.is_valid is False
    assert len(result.errors) > 0
    assert "confidence" in str(result.errors).lower()


def test_buy_without_take_profit_rejected():
    """Test that buy action without take_profit levels is rejected"""
    strategy = StockStrategy(
        ticker="AAPL",
        action="buy",
        take_profit=[],  # Empty take_profit for buy action
        stop_loss=[StopLossLevel(pct=-3.0, sell_ratio=1.0)],
        rationale="Missing take profit",
        confidence=0.8,
    )
    output = AIPromptOutput(market_summary="Market is bullish", strategies=[strategy])
    result = validate_ai_output(output)
    assert isinstance(result, ValidationResult)
    assert result.is_valid is False
    assert len(result.errors) > 0
    assert "take_profit" in str(result.errors).lower()


def test_full_exit_with_stop_loss_rejected():
    """Test that full_exit action with stop_loss levels is rejected"""
    strategy = StockStrategy(
        ticker="AAPL",
        action="full_exit",
        take_profit=[],
        stop_loss=[
            # Should not have stop_loss for full_exit
            StopLossLevel(pct=-3.0, sell_ratio=1.0)
        ],
        rationale="Full exit strategy",
        confidence=0.8,
    )
    output = AIPromptOutput(market_summary="Market is bearish", strategies=[strategy])
    result = validate_ai_output(output)
    assert isinstance(result, ValidationResult)
    assert result.is_valid is False
    assert len(result.errors) > 0
    assert "stop_loss" in str(result.errors).lower()


def test_validation_returns_result_not_exception():
    """Test that validation returns ValidationResult, not exception"""
    # Create invalid strategy (multiple validation errors)
    strategy = StockStrategy(
        ticker="AAPL",
        action="buy",
        take_profit=[],  # Invalid: buy without take_profit
        stop_loss=[],
        rationale="Invalid strategy",
        confidence=0.1,  # Invalid: too low confidence
    )
    output = AIPromptOutput(market_summary="Test", strategies=[strategy])

    # Should return ValidationResult, not raise exception
    result = validate_ai_output(output)
    assert isinstance(result, ValidationResult)
    assert result.is_valid is False
    assert isinstance(result.errors, list)
    assert len(result.errors) >= 2  # Should have multiple errors
