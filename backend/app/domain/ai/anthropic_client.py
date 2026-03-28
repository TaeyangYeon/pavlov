"""Real Anthropic API client implementing AIClient interface."""
import asyncio
import json

import anthropic

from app.domain.ai.client import AIClient
from app.domain.ai.exceptions import AICallError, AIConfigError, AIResponseParseError
from app.domain.ai.schemas import AIPromptOutput

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
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                response = await self._client.messages.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    messages=[{"role": "user", "content": prompt}],
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

