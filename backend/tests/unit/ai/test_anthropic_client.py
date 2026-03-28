"""Unit tests for AnthropicClient (TDD Red phase)."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.domain.ai.anthropic_client import AnthropicClient
from app.domain.ai.exceptions import AICallError, AIConfigError, AIResponseParseError
from app.domain.ai.schemas import AIPromptOutput


class TestAnthropicClient:
    """Test AnthropicClient implementation."""

    def test_client_raises_on_missing_api_key(self):
        """Test that AnthropicClient raises AIConfigError when API key is missing."""
        with pytest.raises(AIConfigError, match="ANTHROPIC_API_KEY is required"):
            AnthropicClient(api_key="")

    @pytest.mark.asyncio
    @patch("anthropic.AsyncAnthropic")
    async def test_client_calls_anthropic_sdk(self, mock_anthropic_class):
        """Test that client calls Anthropic SDK with correct parameters."""
        # Setup mock
        mock_client = AsyncMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"market_summary": "테스트", "strategies": []}')]
        mock_client.messages.create.return_value = mock_response

        # Test
        client = AnthropicClient(api_key="test-key")
        await client.call("test prompt")

        # Verify SDK called correctly
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]

        assert call_kwargs["model"] == "claude-sonnet-4-5"
        assert call_kwargs["max_tokens"] == 2000
        assert call_kwargs["temperature"] == 0.3
        assert call_kwargs["messages"] == [{"role": "user", "content": "test prompt"}]

    @pytest.mark.asyncio
    @patch("anthropic.AsyncAnthropic")
    async def test_client_returns_parsed_output(self, mock_anthropic_class):
        """Test that client returns correctly parsed AIPromptOutput."""
        # Setup mock with valid response
        mock_client = AsyncMock()
        mock_anthropic_class.return_value = mock_client

        valid_response = {
            "market_summary": "테스트 시장 분석",
            "strategies": [
                {
                    "ticker": "005930",
                    "action": "buy",
                    "take_profit": [{"pct": 10.0, "sell_ratio": 0.3}],
                    "stop_loss": [{"pct": -5.0, "sell_ratio": 0.5}],
                    "rationale": "테스트 근거",
                    "confidence": 0.8
                }
            ]
        }

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(valid_response))]
        mock_client.messages.create.return_value = mock_response

        # Test
        client = AnthropicClient(api_key="test-key")
        result = await client.call("test prompt")

        # Verify result
        assert isinstance(result, AIPromptOutput)
        assert result.market_summary == "테스트 시장 분석"
        assert len(result.strategies) == 1
        assert result.strategies[0].ticker == "005930"

    @pytest.mark.asyncio
    @patch("anthropic.AsyncAnthropic")
    async def test_client_strips_markdown_fences(self, mock_anthropic_class):
        """Test that client strips markdown code fences from response."""
        # Setup mock with markdown wrapped response
        mock_client = AsyncMock()
        mock_anthropic_class.return_value = mock_client

        valid_response = {"market_summary": "테스트", "strategies": []}
        wrapped_response = f"```json\n{json.dumps(valid_response)}\n```"

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=wrapped_response)]
        mock_client.messages.create.return_value = mock_response

        # Test
        client = AnthropicClient(api_key="test-key")
        result = await client.call("test prompt")

        # Verify markdown was stripped and parsed correctly
        assert isinstance(result, AIPromptOutput)
        assert result.market_summary == "테스트"

    @pytest.mark.asyncio
    @patch("anthropic.AsyncAnthropic")
    async def test_client_raises_on_invalid_json(self, mock_anthropic_class):
        """Test that client raises AIResponseParseError on invalid JSON."""
        # Setup mock with invalid JSON
        mock_client = AsyncMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="This is not JSON")]
        mock_client.messages.create.return_value = mock_response

        # Test
        client = AnthropicClient(api_key="test-key")

        with pytest.raises(AIResponseParseError, match="JSON decode failed"):
            await client.call("test prompt")

    @pytest.mark.asyncio
    @patch("anthropic.AsyncAnthropic")
    async def test_client_raises_on_pydantic_validation_failure(self, mock_anthropic_class):
        """Test that client raises AIResponseParseError on Pydantic validation failure."""
        # Setup mock with valid JSON but wrong schema
        mock_client = AsyncMock()
        mock_anthropic_class.return_value = mock_client

        invalid_response = {
            "market_summary": "테스트",
            "strategies": [
                {
                    "ticker": "005930",
                    "action": "buy",
                    "confidence": 2.0  # Invalid: should be 0.0-1.0
                }
            ]
        }

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(invalid_response))]
        mock_client.messages.create.return_value = mock_response

        # Test
        client = AnthropicClient(api_key="test-key")

        with pytest.raises(AIResponseParseError, match="Schema validation failed"):
            await client.call("test prompt")

    @pytest.mark.asyncio
    @patch("anthropic.AsyncAnthropic")
    @patch("asyncio.sleep")
    async def test_client_retries_on_rate_limit(self, mock_sleep, mock_anthropic_class):
        """Test that client retries on RateLimitError."""
        # Setup mock that fails once then succeeds
        mock_client = AsyncMock()
        mock_anthropic_class.return_value = mock_client

        # Import anthropic after patching to avoid import errors
        import anthropic

        valid_response = {"market_summary": "테스트", "strategies": []}
        mock_success_response = MagicMock()
        mock_success_response.content = [MagicMock(text=json.dumps(valid_response))]

        mock_client.messages.create.side_effect = [
            anthropic.RateLimitError(
                "Rate limited", response=MagicMock(), body={"error": "rate_limit"}
            ),
            mock_success_response
        ]

        # Test
        client = AnthropicClient(api_key="test-key")
        result = await client.call("test prompt")

        # Verify retry behavior
        assert mock_client.messages.create.call_count == 2
        mock_sleep.assert_called_once_with(1.0)  # First retry delay
        assert isinstance(result, AIPromptOutput)

    @pytest.mark.asyncio
    @patch("anthropic.AsyncAnthropic")
    @patch("asyncio.sleep")
    async def test_client_retries_on_connection_error(self, mock_sleep, mock_anthropic_class):
        """Test that client retries on APIConnectionError."""
        # Setup mock that fails twice then succeeds
        mock_client = AsyncMock()
        mock_anthropic_class.return_value = mock_client

        import anthropic

        valid_response = {"market_summary": "테스트", "strategies": []}
        mock_success_response = MagicMock()
        mock_success_response.content = [MagicMock(text=json.dumps(valid_response))]

        mock_client.messages.create.side_effect = [
            anthropic.APIConnectionError(request=MagicMock()),
            anthropic.APIConnectionError(request=MagicMock()),
            mock_success_response
        ]

        # Test
        client = AnthropicClient(api_key="test-key")
        result = await client.call("test prompt")

        # Verify retry behavior
        assert mock_client.messages.create.call_count == 3
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1.0)  # First retry delay
        mock_sleep.assert_any_call(2.0)  # Second retry delay
        assert isinstance(result, AIPromptOutput)

    @pytest.mark.asyncio
    @patch("anthropic.AsyncAnthropic")
    @patch("asyncio.sleep")
    async def test_client_raises_after_max_retries(self, mock_sleep, mock_anthropic_class):
        """Test that client raises AICallError after max retries."""
        # Setup mock that always fails
        mock_client = AsyncMock()
        mock_anthropic_class.return_value = mock_client

        import anthropic

        mock_client.messages.create.side_effect = [
            anthropic.RateLimitError(
                "Rate limited", response=MagicMock(), body={"error": "rate_limit"}
            ),
            anthropic.RateLimitError(
                "Rate limited", response=MagicMock(), body={"error": "rate_limit"}
            ),
            anthropic.RateLimitError(
                "Rate limited", response=MagicMock(), body={"error": "rate_limit"}
            )
        ]

        # Test
        client = AnthropicClient(api_key="test-key")

        with pytest.raises(AICallError) as exc_info:
            await client.call("test prompt")

        # Verify exception details
        assert exc_info.value.attempts == 3
        assert "Rate limited" in exc_info.value.last_error
        assert mock_client.messages.create.call_count == 3
        assert mock_sleep.call_count == 2  # Only sleep between retries, not after final failure

    @pytest.mark.asyncio
    @patch("anthropic.AsyncAnthropic")
    async def test_client_does_not_retry_on_auth_error(self, mock_anthropic_class):
        """Test that client does not retry on AuthenticationError."""
        # Setup mock that fails with auth error
        mock_client = AsyncMock()
        mock_anthropic_class.return_value = mock_client

        import anthropic

        mock_client.messages.create.side_effect = anthropic.AuthenticationError(
            "Invalid API key", response=MagicMock(), body={"error": "auth_error"}
        )

        # Test
        client = AnthropicClient(api_key="test-key")

        with pytest.raises(AICallError) as exc_info:
            await client.call("test prompt")

        # Verify no retry
        assert mock_client.messages.create.call_count == 1
        assert exc_info.value.attempts == 1
        assert "Invalid API key" in exc_info.value.last_error

    @pytest.mark.asyncio
    @patch("anthropic.AsyncAnthropic")
    @patch("asyncio.sleep")
    async def test_client_exponential_backoff_timing(self, mock_sleep, mock_anthropic_class):
        """Test that client uses correct exponential backoff timing."""
        # Setup mock that fails twice then succeeds
        mock_client = AsyncMock()
        mock_anthropic_class.return_value = mock_client

        import anthropic

        valid_response = {"market_summary": "테스트", "strategies": []}
        mock_success_response = MagicMock()
        mock_success_response.content = [MagicMock(text=json.dumps(valid_response))]

        mock_client.messages.create.side_effect = [
            anthropic.RateLimitError(
                "Rate limited", response=MagicMock(), body={"error": "rate_limit"}
            ),
            anthropic.RateLimitError(
                "Rate limited again", response=MagicMock(), body={"error": "rate_limit"}
            ),
            mock_success_response
        ]

        # Test
        client = AnthropicClient(api_key="test-key")
        await client.call("test prompt")

        # Verify exponential backoff: 1s, 2s
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1.0)
        mock_sleep.assert_any_call(2.0)

