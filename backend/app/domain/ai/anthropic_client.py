"""Real Anthropic API client implementing AIClient interface."""
import asyncio
import json

import anthropic

from app.core.config import get_settings
from app.core.metrics import get_metrics_collector
from app.domain.ai.client import AIClient
from app.domain.ai.exceptions import AICallError, AIConfigError, AIResponseParseError
from app.domain.ai.schemas import AIPromptOutput
from app.infra.ai.cost_tracker import AICostTracker

# Constants for API configuration
MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 2000
TEMPERATURE = 0.3
MAX_RETRIES = 3
RETRY_DELAYS = [1.0, 2.0, 4.0]  # exponential backoff

# Errors that should trigger retry logic
RETRYABLE_ERRORS = (
    anthropic.APIConnectionError,
    anthropic.RateLimitError,
    anthropic.InternalServerError,
)


class AnthropicClient(AIClient):
    """
    Real Anthropic API client implementing AIClient interface.
    Single responsibility: API call with retry logic.
    Prompt building and validation are separate concerns.
    """

    def __init__(self, api_key: str):
        if not api_key:
            raise AIConfigError("ANTHROPIC_API_KEY is required but not set")
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def call(self, prompt: str) -> AIPromptOutput:
        """
        Call Claude API with retry and parse response.
        Max 3 attempts with exponential backoff.
        """
        cost_tracker = AICostTracker()
        metrics = get_metrics_collector()
        settings = get_settings()

        # Pre-flight: compress prompt
        compressed = cost_tracker.compress_prompt(prompt)
        estimated_tokens = cost_tracker.estimate_tokens(compressed)
        if estimated_tokens > 3000:
            print(
                f"[AIClient] Large prompt warning: "
                f"~{estimated_tokens} tokens estimated"
            )

        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                response = await self._client.messages.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    messages=[{"role": "user", "content": compressed}],  # use compressed
                )

                # Track usage
                usage = response.usage
                cost = cost_tracker.calculate_cost(
                    usage.input_tokens,
                    usage.output_tokens,
                )

                print(
                    f"[AIClient] Tokens: "
                    f"in={usage.input_tokens}, "
                    f"out={usage.output_tokens}, "
                    f"cost=${cost:.6f}"
                )

                # Alert if over threshold
                if cost_tracker.is_above_alert_threshold(
                    cost,
                    settings.ai_cost_alert_threshold_usd
                ):
                    print(
                        f"[AIClient] ⚠️ Cost alert: "
                        f"${cost:.6f} exceeds "
                        f"${settings.ai_cost_alert_threshold_usd}"
                    )

                # Record in metrics
                metrics.record_ai_call(
                    market="unknown",  # set by caller if needed
                    input_tokens=usage.input_tokens,
                    output_tokens=usage.output_tokens,
                    cost_usd=cost,
                )

                return self._parse_response(response)

            except RETRYABLE_ERRORS as e:
                last_error = str(e)
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAYS[attempt])
                continue

            except (
                anthropic.AuthenticationError,
                anthropic.BadRequestError,
            ) as e:
                raise AICallError(attempts=attempt + 1, last_error=str(e)) from e

        raise AICallError(
            attempts=MAX_RETRIES, last_error=last_error or "Unknown error"
        )

    def _parse_response(self, response) -> AIPromptOutput:
        """
        Extract, clean, and validate AI response.
        Strips markdown fences before JSON parsing.
        """
        raw_text = response.content[0].text

        # Strip markdown code fences
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1])

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise AIResponseParseError(
                reason=f"JSON decode failed: {e}", raw_response=raw_text[:200]
            ) from e

        try:
            return AIPromptOutput(**data)
        except Exception as e:
            raise AIResponseParseError(
                reason=f"Schema validation failed: {e}", raw_response=raw_text[:200]
            ) from e

