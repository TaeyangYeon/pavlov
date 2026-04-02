"""
AI Cost Tracker for Step 26: Performance Optimization.
Tracks AI API usage and estimated cost using Anthropic Claude pricing.
"""

import re
from decimal import Decimal


# Anthropic Claude Sonnet 4.5 pricing (as of 2025)
INPUT_PRICE_PER_1M_USD = Decimal("3.00")
OUTPUT_PRICE_PER_1M_USD = Decimal("15.00")
PRECISION = Decimal("0.000001")  # 6 decimal places


class AICostTracker:
    """
    Tracks AI API usage and estimated cost.
    Uses token counts from Anthropic API response.
    """

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
    ) -> Decimal:
        """
        Calculate cost for one API call.
        Returns USD cost with 6 decimal precision.
        """
        input_cost = (
            Decimal(str(input_tokens))
            / Decimal("1000000")
            * INPUT_PRICE_PER_1M_USD
        ).quantize(PRECISION)

        output_cost = (
            Decimal(str(output_tokens))
            / Decimal("1000000")
            * OUTPUT_PRICE_PER_1M_USD
        ).quantize(PRECISION)

        return (input_cost + output_cost).quantize(PRECISION)

    def is_above_alert_threshold(
        self,
        cost_usd: Decimal,
        threshold_usd: float,
    ) -> bool:
        """Check if cost exceeds alert threshold."""
        return cost_usd > Decimal(str(threshold_usd))

    def estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation (4 chars ≈ 1 token).
        Used for pre-flight check before API call.
        """
        return max(1, len(text) // 4)

    def compress_prompt(self, prompt: str) -> str:
        """
        Reduce prompt size without losing structure.
        Removes redundant whitespace.
        """
        # Remove multiple blank lines (3+ newlines -> 2 newlines)
        compressed = re.sub(r'\n{3,}', '\n\n', prompt)
        
        # Remove trailing whitespace per line
        compressed = '\n'.join(
            line.rstrip()
            for line in compressed.split('\n')
        )
        
        return compressed.strip()