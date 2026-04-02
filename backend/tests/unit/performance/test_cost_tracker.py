"""
Unit tests for AI Cost Tracker (Step 26: Performance Optimization)
Tests token-based cost calculation using Anthropic Claude pricing.
"""

import pytest
from decimal import Decimal
from app.infra.ai.cost_tracker import AICostTracker


class TestAICostTracker:
    """Test the AICostTracker class."""

    def test_cost_calculation_known_values(self):
        """Test cost calculation with known token values."""
        tracker = AICostTracker()
        
        # Known values for exact calculation
        input_tokens = 1000
        output_tokens = 200
        
        # Expected calculation:
        # input_cost = 1000/1,000,000 * 3.00 = 0.003000
        # output_cost = 200/1,000,000 * 15.00 = 0.003000
        # total_cost = 0.006000
        
        cost = tracker.calculate_cost(input_tokens, output_tokens)
        expected = Decimal("0.006000")
        
        assert cost == expected
        assert isinstance(cost, Decimal)

    def test_cost_zero_tokens(self):
        """Test cost calculation with zero tokens."""
        tracker = AICostTracker()
        cost = tracker.calculate_cost(0, 0)
        assert cost == Decimal("0.000000")

    def test_cost_large_token_count(self):
        """Test cost calculation with larger token counts."""
        tracker = AICostTracker()
        
        input_tokens = 10000
        output_tokens = 2000
        
        # Expected calculation:
        # input_cost = 10000/1,000,000 * 3.00 = 0.030000
        # output_cost = 2000/1,000,000 * 15.00 = 0.030000
        # total = 0.060000
        
        cost = tracker.calculate_cost(input_tokens, output_tokens)
        expected = Decimal("0.060000")
        
        assert cost == expected

    def test_cost_exceeds_alert_threshold(self):
        """Test detection of cost exceeding alert threshold."""
        tracker = AICostTracker()
        
        # Large token count that exceeds $0.10
        input_tokens = 20000
        output_tokens = 5000
        
        # Expected calculation:
        # input_cost = 20000/1,000,000 * 3.00 = 0.060000
        # output_cost = 5000/1,000,000 * 15.00 = 0.075000
        # total = 0.135000 (exceeds $0.10)
        
        cost = tracker.calculate_cost(input_tokens, output_tokens)
        expected = Decimal("0.135000")
        
        assert cost == expected
        assert tracker.is_above_alert_threshold(cost, 0.10) is True

    def test_cost_below_alert_threshold(self):
        """Test detection of cost below alert threshold."""
        tracker = AICostTracker()
        
        input_tokens = 1000
        output_tokens = 200
        cost = tracker.calculate_cost(input_tokens, output_tokens)
        
        assert tracker.is_above_alert_threshold(cost, 0.10) is False

    def test_cost_precision_6_decimal_places(self):
        """Test that cost is calculated with 6 decimal places precision."""
        tracker = AICostTracker()
        
        # Use fractional tokens that would create precision issues
        input_tokens = 1
        output_tokens = 1
        
        cost = tracker.calculate_cost(input_tokens, output_tokens)
        
        # Should have exactly 6 decimal places
        cost_str = str(cost)
        decimal_part = cost_str.split('.')[1] if '.' in cost_str else ''
        assert len(decimal_part) == 6

    def test_token_estimation(self):
        """Test rough token estimation from text."""
        tracker = AICostTracker()
        
        # Test various text lengths
        short_text = "hello world"  # 11 chars
        estimated = tracker.estimate_tokens(short_text)
        assert estimated >= 2  # 11/4 = 2.75, should round up
        
        medium_text = "a" * 100  # 100 chars
        estimated = tracker.estimate_tokens(medium_text)
        assert estimated == 25  # 100/4 = 25
        
        empty_text = ""
        estimated = tracker.estimate_tokens(empty_text)
        assert estimated == 1  # minimum 1 token

    def test_prompt_compression(self):
        """Test prompt compression functionality."""
        tracker = AICostTracker()
        
        # Test removing multiple blank lines
        prompt_with_blanks = "Line 1\n\n\n\nLine 2\n\n\n\nLine 3"
        compressed = tracker.compress_prompt(prompt_with_blanks)
        expected = "Line 1\n\nLine 2\n\nLine 3"
        assert compressed == expected
        
        # Test removing trailing whitespace
        prompt_with_spaces = "Line 1   \n  Line 2  \n   Line 3   "
        compressed = tracker.compress_prompt(prompt_with_spaces)
        expected = "Line 1\n  Line 2\n   Line 3"
        assert compressed == expected
        
        # Test that compression reduces size
        original_size = len(prompt_with_blanks)
        compressed_size = len(compressed)
        assert compressed_size < original_size

    def test_pricing_constants(self):
        """Test that pricing constants are correct."""
        from app.infra.ai.cost_tracker import INPUT_PRICE_PER_1M_USD, OUTPUT_PRICE_PER_1M_USD
        
        # Verify Claude Sonnet 4.5 pricing as of 2025
        assert INPUT_PRICE_PER_1M_USD == Decimal("3.00")
        assert OUTPUT_PRICE_PER_1M_USD == Decimal("15.00")

    def test_various_token_combinations(self):
        """Test cost calculation with various token combinations."""
        tracker = AICostTracker()
        
        test_cases = [
            # (input_tokens, output_tokens, expected_cost)
            (100, 50, Decimal("0.001050")),  # 0.0003 + 0.00075
            (500, 100, Decimal("0.003000")),  # 0.0015 + 0.0015
            (2000, 800, Decimal("0.018000")), # 0.006 + 0.012
            (1, 1, Decimal("0.000018")),     # 0.000003 + 0.000015
        ]
        
        for input_tokens, output_tokens, expected_cost in test_cases:
            actual_cost = tracker.calculate_cost(input_tokens, output_tokens)
            assert actual_cost == expected_cost, f"Failed for {input_tokens}, {output_tokens}"

    def test_alert_threshold_edge_cases(self):
        """Test alert threshold detection at edge cases."""
        tracker = AICostTracker()
        
        threshold = 0.10
        
        # Exactly at threshold
        cost_exact = Decimal("0.100000")
        assert tracker.is_above_alert_threshold(cost_exact, threshold) is False
        
        # Just above threshold
        cost_above = Decimal("0.100001")
        assert tracker.is_above_alert_threshold(cost_above, threshold) is True
        
        # Just below threshold
        cost_below = Decimal("0.099999")
        assert tracker.is_above_alert_threshold(cost_below, threshold) is False

    def test_very_large_token_counts(self):
        """Test cost calculation with very large token counts."""
        tracker = AICostTracker()
        
        # 1 million input tokens, 100k output tokens
        input_tokens = 1_000_000
        output_tokens = 100_000
        
        # Expected: 1M/1M * 3.00 + 100K/1M * 15.00 = 3.00 + 1.50 = 4.50
        cost = tracker.calculate_cost(input_tokens, output_tokens)
        expected = Decimal("4.500000")
        
        assert cost == expected

    def test_cost_calculation_preserves_decimal_precision(self):
        """Test that Decimal precision is preserved throughout calculation."""
        tracker = AICostTracker()
        
        # Use prime numbers to avoid rounding artifacts
        input_tokens = 1337
        output_tokens = 421
        
        cost = tracker.calculate_cost(input_tokens, output_tokens)
        
        # Verify it's a Decimal with proper precision
        assert isinstance(cost, Decimal)
        assert cost.as_tuple().exponent == -6  # 6 decimal places