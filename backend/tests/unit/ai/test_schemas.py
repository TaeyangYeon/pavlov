import pytest
from app.domain.ai.schemas import (
    AIPromptInput,
    AIPromptOutput,
    StockIndicators,
    StockStrategy,
)
from pydantic import ValidationError


def test_valid_stock_input_schema():
    """Test valid StockIndicators creation"""
    stock = StockIndicators(
        ticker="AAPL",
        name="Apple Inc.",
        market="NASDAQ",
        close=150.0,
        volume_ratio=1.5,
        rsi_14=65.0,
        ma_20=145.0,
        ma_60=140.0,
        atr_14=2.5,
    )
    assert stock.ticker == "AAPL"
    assert stock.rsi_14 == 65.0


def test_invalid_rsi_out_of_range():
    """Test RSI validation - must be 0~100"""
    with pytest.raises(ValidationError) as exc_info:
        StockIndicators(
            ticker="AAPL",
            name="Apple Inc.",
            market="NASDAQ",
            close=150.0,
            volume_ratio=1.5,
            rsi_14=105.0,  # Invalid: > 100
            ma_20=145.0,
            ma_60=140.0,
            atr_14=2.5,
        )
    assert "rsi_14" in str(exc_info.value)


def test_invalid_confidence_out_of_range():
    """Test confidence validation - must be 0.0~1.0"""
    with pytest.raises(ValidationError) as exc_info:
        StockStrategy(
            ticker="AAPL",
            action="buy",
            take_profit=[],
            stop_loss=[],
            rationale="Test rationale",
            confidence=1.5,  # Invalid: > 1.0
        )
    assert "confidence" in str(exc_info.value)


def test_rationale_max_length():
    """Test rationale max length validation - max 100 chars"""
    long_rationale = "x" * 101  # 101 characters
    with pytest.raises(ValidationError) as exc_info:
        StockStrategy(
            ticker="AAPL",
            action="buy",
            take_profit=[],
            stop_loss=[],
            rationale=long_rationale,
            confidence=0.8,
        )
    assert "rationale" in str(exc_info.value)


def test_market_summary_max_length():
    """Test market_summary max length validation - max 200 chars"""
    long_summary = "x" * 201  # 201 characters
    with pytest.raises(ValidationError) as exc_info:
        AIPromptOutput(market_summary=long_summary, strategies=[])
    assert "market_summary" in str(exc_info.value)


def test_action_literal_validation():
    """Test action literal validation - only allowed actions"""
    with pytest.raises(ValidationError) as exc_info:
        StockStrategy(
            ticker="AAPL",
            action="invalid_action",  # Invalid action
            take_profit=[],
            stop_loss=[],
            rationale="Test",
            confidence=0.8,
        )
    assert "action" in str(exc_info.value)


def test_empty_filtered_stocks_allowed():
    """Test edge case - empty filtered_stocks should be allowed"""
    prompt_input = AIPromptInput(
        market="NASDAQ",
        date="2024-01-01",
        filtered_stocks=[],  # Empty list should be allowed
        held_positions=[],
    )
    assert prompt_input.filtered_stocks == []
