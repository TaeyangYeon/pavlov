from app.domain.ai.prompt_builder import build_prompt
from app.domain.ai.schemas import AIPromptInput, HeldPosition, StockIndicators


def test_prompt_contains_market_type():
    """Test that prompt contains market type"""
    prompt_input = AIPromptInput(
        market="NASDAQ", date="2024-01-01", filtered_stocks=[], held_positions=[]
    )
    prompt = build_prompt(prompt_input)
    assert "NASDAQ" in prompt
    assert isinstance(prompt, str)


def test_prompt_contains_all_tickers():
    """Test that prompt contains all stock tickers"""
    stocks = [
        StockIndicators(
            ticker="AAPL",
            name="Apple Inc.",
            market="NASDAQ",
            close=150.0,
            volume_ratio=1.5,
            rsi_14=65.0,
            ma_20=145.0,
            ma_60=140.0,
            atr_14=2.5,
        ),
        StockIndicators(
            ticker="GOOGL",
            name="Alphabet Inc.",
            market="NASDAQ",
            close=2800.0,
            volume_ratio=1.2,
            rsi_14=70.0,
            ma_20=2750.0,
            ma_60=2700.0,
            atr_14=50.0,
        ),
    ]
    prompt_input = AIPromptInput(
        market="NASDAQ", date="2024-01-01", filtered_stocks=stocks, held_positions=[]
    )
    prompt = build_prompt(prompt_input)
    assert "AAPL" in prompt
    assert "GOOGL" in prompt


def test_prompt_contains_held_positions():
    """Test that prompt contains held positions"""
    positions = [
        HeldPosition(ticker="AAPL", avg_price=140.0, quantity=100, current_pnl_pct=7.14)
    ]
    prompt_input = AIPromptInput(
        market="NASDAQ", date="2024-01-01", filtered_stocks=[], held_positions=positions
    )
    prompt = build_prompt(prompt_input)
    assert "AAPL" in prompt
    assert "140.0" in prompt or "140" in prompt
    assert "100" in prompt


def test_prompt_format_is_string():
    """Test that prompt returns a string"""
    prompt_input = AIPromptInput(
        market="NASDAQ", date="2024-01-01", filtered_stocks=[], held_positions=[]
    )
    prompt = build_prompt(prompt_input)
    assert isinstance(prompt, str)
    assert len(prompt) > 0


def test_prompt_with_empty_positions():
    """Test edge case - prompt with empty positions"""
    prompt_input = AIPromptInput(
        market="NASDAQ",
        date="2024-01-01",
        filtered_stocks=[],
        held_positions=[],  # Empty positions
    )
    prompt = build_prompt(prompt_input)
    assert isinstance(prompt, str)
    assert "NASDAQ" in prompt
    assert len(prompt) > 0
