from abc import ABC, abstractmethod

from app.domain.ai.schemas import (
    AIPromptOutput,
    StockStrategy,
    StopLossLevel,
)


class AIClient(ABC):
    """
    Abstract base class for AI client implementations.

    This defines the contract for AI API interactions.
    Real implementation will be provided in Step 9.
    """

    @abstractmethod
    async def call(self, prompt: str) -> AIPromptOutput:
        """
        Call AI API with the given prompt and return parsed output.

        Args:
            prompt: Complete prompt string from prompt_builder

        Returns:
            AIPromptOutput: Validated AI response

        Raises:
            AIClientError: When API call fails or response is invalid
        """
        pass


class MockAIClient(AIClient):
    """
    Mock implementation for testing and development.

    Returns hardcoded valid response for testing purposes.
    Real implementation in Step 9.
    """

    async def call(self, prompt: str) -> AIPromptOutput:
        """
        Return a hardcoded valid response for testing.

        This mock always returns a valid strategy to test the pipeline.
        """
        return AIPromptOutput(
            market_summary=(
                "Mock market analysis: Overall market shows mixed signals "
                "with moderate volatility."
            ),
            strategies=[
                StockStrategy(
                    ticker="AAPL",
                    action="hold",
                    take_profit=[],
                    stop_loss=[StopLossLevel(pct=-5.0, sell_ratio=1.0)],
                    rationale=(
                        "Mock strategy: Technical indicators suggest "
                        "consolidation phase."
                    ),
                    confidence=0.7,
                )
            ],
        )


# Real implementation will replace this in Step 9
# from openai import AsyncOpenAI
# from anthropic import AsyncAnthropic
# etc...
