"""Enhanced unit tests for validators.py with hallucination defense."""
import pytest
from app.domain.ai.schemas import (
    AIPromptOutput,
    StockStrategy,
    StopLossLevel,
    TakeProfitLevel,
)
from app.domain.ai.validators import validate_ai_output_with_context


class TestValidatorsEnhanced:
    """Test enhanced validation with ticker cross-check and hallucination defense."""

    def test_ticker_cross_check_passes_valid_tickers(self):
        """Test that strategies with valid tickers pass validation."""
        # Setup filtered stocks
        valid_tickers = ["AAPL", "GOOGL", "MSFT"]

        # Create AI output with strategies for valid tickers
        output = AIPromptOutput(
            market_summary="Valid tickers strategy",
            strategies=[
                StockStrategy(
                    ticker="AAPL",
                    action="buy",
                    take_profit=[TakeProfitLevel(pct=10.0, sell_ratio=0.5)],
                    stop_loss=[StopLossLevel(pct=-5.0, sell_ratio=1.0)],
                    rationale="Valid strategy",
                    confidence=0.8
                ),
                StockStrategy(
                    ticker="GOOGL",
                    action="hold",
                    take_profit=[],
                    stop_loss=[StopLossLevel(pct=-3.0, sell_ratio=0.5)],
                    rationale="Hold strategy",
                    confidence=0.7
                )
            ]
        )

        # Test
        result = validate_ai_output_with_context(output, valid_tickers)

        # Verify
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_ticker_cross_check_rejects_hallucinated_tickers(self):
        """Test that AI-invented tickers are rejected as hallucinations."""
        # Setup filtered stocks
        valid_tickers = ["AAPL", "GOOGL"]

        # Create AI output with hallucinated ticker
        output = AIPromptOutput(
            market_summary="Contains hallucinated ticker",
            strategies=[
                StockStrategy(
                    ticker="AAPL",
                    action="buy",
                    take_profit=[TakeProfitLevel(pct=10.0, sell_ratio=0.5)],
                    stop_loss=[StopLossLevel(pct=-5.0, sell_ratio=1.0)],
                    rationale="Valid strategy",
                    confidence=0.8
                ),
                StockStrategy(
                    ticker="FAKE123",  # Hallucinated ticker
                    action="buy",
                    take_profit=[TakeProfitLevel(pct=15.0, sell_ratio=0.7)],
                    stop_loss=[StopLossLevel(pct=-8.0, sell_ratio=1.0)],
                    rationale="Hallucinated strategy",
                    confidence=0.9
                )
            ]
        )

        # Test
        result = validate_ai_output_with_context(output, valid_tickers)

        # Verify
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "FAKE123" in result.errors[0]
        assert "not in filtered stocks" in result.errors[0]
        assert "hallucination" in result.errors[0]

    def test_take_profit_pct_enforced_by_pydantic(self):
        """Test that take_profit percentages are enforced by Pydantic schema."""
        # Verify that Pydantic prevents creation of invalid TakeProfitLevel
        with pytest.raises(ValueError, match="Input should be greater than 0"):
            TakeProfitLevel(pct=-5.0, sell_ratio=0.5)

    def test_stop_loss_pct_must_be_negative_enforced_by_pydantic(self):
        """Test that positive stop_loss percentages are prevented by Pydantic schema."""
        # Verify that Pydantic prevents creation of invalid StopLossLevel
        with pytest.raises(ValueError, match="Input should be less than 0"):
            StopLossLevel(pct=5.0, sell_ratio=1.0)

    def test_take_profit_sell_ratio_sum_exceeds_one(self):
        """Test that take_profit sell_ratio sum cannot exceed 1.0."""
        valid_tickers = ["AAPL"]

        output = AIPromptOutput(
            market_summary="TP ratio sum exceeds 1.0",
            strategies=[
                StockStrategy(
                    ticker="AAPL",
                    action="buy",
                    take_profit=[
                        TakeProfitLevel(pct=10.0, sell_ratio=0.6),
                        TakeProfitLevel(pct=20.0, sell_ratio=0.6)  # Total = 1.2 > 1.0
                    ],
                    stop_loss=[StopLossLevel(pct=-5.0, sell_ratio=1.0)],
                    rationale="Invalid TP ratio",
                    confidence=0.8
                )
            ]
        )

        # Test
        result = validate_ai_output_with_context(output, valid_tickers)

        # Verify
        assert result.is_valid is False
        # Should catch this from base validation
        assert any("Take profit sell_ratio total" in error for error in result.errors)

    def test_stop_loss_sell_ratio_sum_exceeds_one(self):
        """Test that stop_loss sell_ratio sum cannot exceed 1.0."""
        valid_tickers = ["AAPL"]

        output = AIPromptOutput(
            market_summary="SL ratio sum exceeds 1.0",
            strategies=[
                StockStrategy(
                    ticker="AAPL",
                    action="buy",
                    take_profit=[TakeProfitLevel(pct=10.0, sell_ratio=0.5)],
                    stop_loss=[
                        StopLossLevel(pct=-3.0, sell_ratio=0.8),
                        StopLossLevel(pct=-8.0, sell_ratio=0.8)  # Total = 1.6 > 1.0
                    ],
                    rationale="Invalid SL ratio",
                    confidence=0.8
                )
            ]
        )

        # Test
        result = validate_ai_output_with_context(output, valid_tickers)

        # Verify
        assert result.is_valid is False
        # Should catch this from base validation
        assert any("Stop loss sell_ratio total" in error for error in result.errors)

    def test_empty_strategies_is_valid(self):
        """Test that empty strategies list is valid (AI has no recommendations)."""
        valid_tickers = ["AAPL", "GOOGL"]

        output = AIPromptOutput(
            market_summary="No strategies today",
            strategies=[]
        )

        # Test
        result = validate_ai_output_with_context(output, valid_tickers)

        # Verify
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_multiple_strategies_all_valid(self):
        """Test that multiple valid strategies all pass."""
        valid_tickers = ["AAPL", "GOOGL", "MSFT"]

        output = AIPromptOutput(
            market_summary="Three valid strategies",
            strategies=[
                StockStrategy(
                    ticker="AAPL",
                    action="buy",
                    take_profit=[TakeProfitLevel(pct=10.0, sell_ratio=0.3)],
                    stop_loss=[StopLossLevel(pct=-5.0, sell_ratio=0.5)],
                    rationale="Strong buy signal",
                    confidence=0.8
                ),
                StockStrategy(
                    ticker="GOOGL",
                    action="hold",
                    take_profit=[],
                    stop_loss=[StopLossLevel(pct=-3.0, sell_ratio=1.0)],
                    rationale="Hold position",
                    confidence=0.6
                ),
                StockStrategy(
                    ticker="MSFT",
                    action="partial_sell",
                    take_profit=[TakeProfitLevel(pct=8.0, sell_ratio=0.4)],
                    stop_loss=[StopLossLevel(pct=-4.0, sell_ratio=0.6)],
                    rationale="Take some profits",
                    confidence=0.7
                )
            ]
        )

        # Test
        result = validate_ai_output_with_context(output, valid_tickers)

        # Verify
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_multiple_strategies_one_invalid(self):
        """Test that one invalid strategy makes entire result invalid."""
        valid_tickers = ["AAPL", "GOOGL"]

        output = AIPromptOutput(
            market_summary="Mixed valid and invalid strategies",
            strategies=[
                StockStrategy(
                    ticker="AAPL",
                    action="buy",
                    take_profit=[TakeProfitLevel(pct=10.0, sell_ratio=0.5)],
                    stop_loss=[StopLossLevel(pct=-5.0, sell_ratio=1.0)],
                    rationale="Valid strategy",
                    confidence=0.8
                ),
                StockStrategy(
                    ticker="INVALID_TICKER",  # Hallucinated
                    action="buy",
                    take_profit=[TakeProfitLevel(pct=15.0, sell_ratio=0.7)],
                    stop_loss=[StopLossLevel(pct=-8.0, sell_ratio=1.0)],
                    rationale="Invalid strategy",
                    confidence=0.9
                ),
                StockStrategy(
                    ticker="GOOGL",
                    action="hold",
                    take_profit=[],
                    stop_loss=[StopLossLevel(pct=-3.0, sell_ratio=1.0)],
                    rationale="Valid hold",
                    confidence=0.6
                )
            ]
        )

        # Test
        result = validate_ai_output_with_context(output, valid_tickers)

        # Verify
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "INVALID_TICKER" in result.errors[0]
        assert "not in filtered stocks" in result.errors[0]

    def test_zero_take_profit_pct_enforced_by_pydantic(self):
        """Test that zero take_profit percentage is prevented by Pydantic schema."""
        # Verify that Pydantic prevents creation of invalid TakeProfitLevel
        with pytest.raises(ValueError, match="Input should be greater than 0"):
            TakeProfitLevel(pct=0.0, sell_ratio=0.5)

    def test_zero_stop_loss_pct_enforced_by_pydantic(self):
        """Test that zero stop_loss percentage is prevented by Pydantic schema."""
        # Verify that Pydantic prevents creation of invalid StopLossLevel
        with pytest.raises(ValueError, match="Input should be less than 0"):
            StopLossLevel(pct=0.0, sell_ratio=1.0)
