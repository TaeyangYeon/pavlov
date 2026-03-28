"""Unit tests for AnalysisPipeline orchestrator."""
from datetime import date
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from app.domain.ai.exceptions import AICallError
from app.domain.ai.pipeline import AnalysisPipeline
from app.domain.ai.schemas import (
    AIPromptInput,
    AIPromptOutput,
    StockIndicators,
    StockStrategy,
    StopLossLevel,
    TakeProfitLevel,
    ValidationResult,
)
from app.infra.db.models.analysis_log import AnalysisLog


class TestAnalysisPipeline:
    """Test AnalysisPipeline orchestrator functionality."""

    @pytest.fixture
    def mock_ai_client(self):
        """Mock AI client for testing."""
        return AsyncMock()

    @pytest.fixture
    def mock_log_repository(self):
        """Mock analysis log repository for testing."""
        repo = AsyncMock()
        repo.save.return_value = AnalysisLog(
            id=uuid4(),
            date=date(2024, 1, 1),
            market="US",
            executed=True,
            ai_response={},
            error_message=None
        )
        return repo

    @pytest.fixture
    def sample_prompt_input(self):
        """Sample prompt input for testing."""
        return AIPromptInput(
            market="US",
            date="2024-01-01",
            filtered_stocks=[
                StockIndicators(
                    ticker="AAPL",
                    name="Apple Inc.",
                    market="US",
                    close=150.0,
                    volume_ratio=1.2,
                    rsi_14=65.0,
                    ma_20=145.0,
                    ma_60=140.0,
                    atr_14=2.5
                ),
                StockIndicators(
                    ticker="GOOGL",
                    name="Alphabet Inc.",
                    market="US",
                    close=2800.0,
                    volume_ratio=0.8,
                    rsi_14=55.0,
                    ma_20=2750.0,
                    ma_60=2700.0,
                    atr_14=50.0
                )
            ],
            held_positions=[]
        )

    @pytest.fixture
    def sample_ai_output(self):
        """Sample AI output for testing."""
        return AIPromptOutput(
            market_summary="Market looking bullish today",
            strategies=[
                StockStrategy(
                    ticker="AAPL",
                    action="buy",
                    take_profit=[TakeProfitLevel(pct=10.0, sell_ratio=0.5)],
                    stop_loss=[StopLossLevel(pct=-5.0, sell_ratio=1.0)],
                    rationale="Strong technical setup",
                    confidence=0.8
                )
            ]
        )

    @pytest.mark.asyncio
    async def test_pipeline_happy_path(
        self,
        mock_ai_client,
        mock_log_repository,
        sample_prompt_input,
        sample_ai_output
    ):
        """Test pipeline happy path with successful AI call and validation."""
        # Setup mocks
        mock_ai_client.call.return_value = sample_ai_output

        with patch('app.domain.ai.pipeline.build_prompt') as mock_build_prompt, \
             patch('app.domain.ai.pipeline.validate_ai_output_with_context') as mock_validate:

            mock_build_prompt.return_value = "test prompt"
            mock_validate.return_value = ValidationResult(is_valid=True, errors=[])

            # Create pipeline
            pipeline = AnalysisPipeline(mock_ai_client, mock_log_repository)

            # Test
            result = await pipeline.run(sample_prompt_input, date(2024, 1, 1))

            # Verify result
            assert result is not None
            assert isinstance(result, AIPromptOutput)
            assert result == sample_ai_output

            # Verify pipeline calls
            mock_build_prompt.assert_called_once_with(sample_prompt_input)
            mock_ai_client.call.assert_called_once_with("test prompt")
            mock_validate.assert_called_once_with(sample_ai_output, ["AAPL", "GOOGL"])

            # Verify log saved
            mock_log_repository.save.assert_called_once_with(
                date=date(2024, 1, 1),
                market="US",
                executed=True,
                ai_response=sample_ai_output.model_dump()
            )

    @pytest.mark.asyncio
    async def test_pipeline_returns_none_on_validation_failure(
        self,
        mock_ai_client,
        mock_log_repository,
        sample_prompt_input,
        sample_ai_output
    ):
        """Test pipeline returns None when validation fails."""
        # Setup mocks
        mock_ai_client.call.return_value = sample_ai_output

        with patch('app.domain.ai.pipeline.build_prompt') as mock_build_prompt, \
             patch('app.domain.ai.pipeline.validate_ai_output_with_context') as mock_validate:

            mock_build_prompt.return_value = "test prompt"
            mock_validate.return_value = ValidationResult(
                is_valid=False,
                errors=["Validation error message"]
            )

            # Create pipeline
            pipeline = AnalysisPipeline(mock_ai_client, mock_log_repository)

            # Test
            result = await pipeline.run(sample_prompt_input, date(2024, 1, 1))

            # Verify result
            assert result is None

            # Verify AI was called but validation failed
            mock_ai_client.call.assert_called_once()
            mock_validate.assert_called_once()

            # Verify log saved with failure
            mock_log_repository.save.assert_called_once_with(
                date=date(2024, 1, 1),
                market="US",
                executed=False,
                error_message="Validation failed: Validation error message"
            )

    @pytest.mark.asyncio
    async def test_pipeline_raises_on_ai_call_failure(
        self,
        mock_ai_client,
        mock_log_repository,
        sample_prompt_input
    ):
        """Test pipeline raises and logs when AI call fails."""
        # Setup mocks
        ai_error = AICallError(attempts=3, last_error="Rate limited")
        mock_ai_client.call.side_effect = ai_error

        with patch('app.domain.ai.pipeline.build_prompt') as mock_build_prompt:
            mock_build_prompt.return_value = "test prompt"

            # Create pipeline
            pipeline = AnalysisPipeline(mock_ai_client, mock_log_repository)

            # Test
            with pytest.raises(AICallError):
                await pipeline.run(sample_prompt_input, date(2024, 1, 1))

            # Verify AI was called
            mock_ai_client.call.assert_called_once_with("test prompt")

            # Verify log saved with error
            mock_log_repository.save.assert_called_once_with(
                date=date(2024, 1, 1),
                market="US",
                executed=False,
                error_message=str(ai_error)
            )

    @pytest.mark.asyncio
    async def test_pipeline_saves_log_on_success(
        self,
        mock_ai_client,
        mock_log_repository,
        sample_prompt_input,
        sample_ai_output
    ):
        """Test that successful pipeline execution saves log with executed=True."""
        # Setup mocks
        mock_ai_client.call.return_value = sample_ai_output

        with patch('app.domain.ai.pipeline.build_prompt'), \
             patch('app.domain.ai.pipeline.validate_ai_output_with_context') as mock_validate:

            mock_validate.return_value = ValidationResult(is_valid=True, errors=[])

            # Create pipeline
            pipeline = AnalysisPipeline(mock_ai_client, mock_log_repository)

            # Test
            await pipeline.run(sample_prompt_input, date(2024, 1, 1))

            # Verify log details
            call_args = mock_log_repository.save.call_args
            assert call_args[1]['executed'] is True
            assert call_args[1]['ai_response'] == sample_ai_output.model_dump()
            assert call_args[1]['date'] == date(2024, 1, 1)
            assert call_args[1]['market'] == "US"

    @pytest.mark.asyncio
    async def test_pipeline_saves_log_on_validation_failure(
        self,
        mock_ai_client,
        mock_log_repository,
        sample_prompt_input,
        sample_ai_output
    ):
        """Test that validation failure saves log with executed=False."""
        # Setup mocks
        mock_ai_client.call.return_value = sample_ai_output

        with patch('app.domain.ai.pipeline.build_prompt'), \
             patch('app.domain.ai.pipeline.validate_ai_output_with_context') as mock_validate:

            mock_validate.return_value = ValidationResult(
                is_valid=False,
                errors=["Ticker not found", "Invalid confidence"]
            )

            # Create pipeline
            pipeline = AnalysisPipeline(mock_ai_client, mock_log_repository)

            # Test
            await pipeline.run(sample_prompt_input, date(2024, 1, 1))

            # Verify log details
            call_args = mock_log_repository.save.call_args
            assert call_args[1]['executed'] is False
            assert "Validation failed: Ticker not found; Invalid confidence" in call_args[1]['error_message']
            assert call_args[1]['date'] == date(2024, 1, 1)
            assert call_args[1]['market'] == "US"

    @pytest.mark.asyncio
    async def test_pipeline_saves_log_on_ai_failure(
        self,
        mock_ai_client,
        mock_log_repository,
        sample_prompt_input
    ):
        """Test that AI call failure saves log with executed=False."""
        # Setup mocks
        ai_error = AICallError(attempts=3, last_error="Connection timeout")
        mock_ai_client.call.side_effect = ai_error

        with patch('app.domain.ai.pipeline.build_prompt'):
            # Create pipeline
            pipeline = AnalysisPipeline(mock_ai_client, mock_log_repository)

            # Test
            with pytest.raises(AICallError):
                await pipeline.run(sample_prompt_input, date(2024, 1, 1))

            # Verify log details
            call_args = mock_log_repository.save.call_args
            assert call_args[1]['executed'] is False
            assert "AI call failed after 3 attempts" in call_args[1]['error_message']
            assert call_args[1]['date'] == date(2024, 1, 1)
            assert call_args[1]['market'] == "US"

    @pytest.mark.asyncio
    async def test_pipeline_calls_prompt_builder(
        self,
        mock_ai_client,
        mock_log_repository,
        sample_prompt_input,
        sample_ai_output
    ):
        """Test that pipeline correctly calls prompt builder with input."""
        # Setup mocks
        mock_ai_client.call.return_value = sample_ai_output

        with patch('app.domain.ai.pipeline.build_prompt') as mock_build_prompt, \
             patch('app.domain.ai.pipeline.validate_ai_output_with_context') as mock_validate:

            mock_build_prompt.return_value = "built prompt string"
            mock_validate.return_value = ValidationResult(is_valid=True, errors=[])

            # Create pipeline
            pipeline = AnalysisPipeline(mock_ai_client, mock_log_repository)

            # Test
            await pipeline.run(sample_prompt_input, date(2024, 1, 1))

            # Verify prompt builder called correctly
            mock_build_prompt.assert_called_once_with(sample_prompt_input)
            mock_ai_client.call.assert_called_once_with("built prompt string")

    @pytest.mark.asyncio
    async def test_pipeline_is_stateless(
        self,
        mock_ai_client,
        mock_log_repository,
        sample_ai_output
    ):
        """Test that pipeline is stateless - no state leaks between calls."""
        # Setup mocks
        mock_ai_client.call.return_value = sample_ai_output

        with patch('app.domain.ai.pipeline.build_prompt') as mock_build_prompt, \
             patch('app.domain.ai.pipeline.validate_ai_output_with_context') as mock_validate:

            mock_build_prompt.return_value = "test prompt"
            mock_validate.return_value = ValidationResult(is_valid=True, errors=[])

            # Create pipeline
            pipeline = AnalysisPipeline(mock_ai_client, mock_log_repository)

            # Create different inputs
            input1 = AIPromptInput(
                market="US",
                date="2024-01-01",
                filtered_stocks=[
                    StockIndicators(
                        ticker="AAPL", name="Apple", market="US", close=150.0,
                        volume_ratio=1.0, rsi_14=60.0, ma_20=145.0, ma_60=140.0, atr_14=2.0
                    )
                ],
                held_positions=[]
            )

            input2 = AIPromptInput(
                market="KR",
                date="2024-01-02",
                filtered_stocks=[
                    StockIndicators(
                        ticker="005930", name="Samsung", market="KR", close=80000.0,
                        volume_ratio=1.5, rsi_14=70.0, ma_20=78000.0, ma_60=76000.0, atr_14=1500.0
                    )
                ],
                held_positions=[]
            )

            # Test first call
            result1 = await pipeline.run(input1, date(2024, 1, 1))

            # Test second call with different input
            result2 = await pipeline.run(input2, date(2024, 1, 2))

            # Verify both calls succeeded
            assert result1 is not None
            assert result2 is not None

            # Verify calls were independent
            assert mock_build_prompt.call_count == 2
            assert mock_ai_client.call.call_count == 2
            assert mock_validate.call_count == 2
            assert mock_log_repository.save.call_count == 2

            # Verify correct inputs were passed
            first_call_input = mock_build_prompt.call_args_list[0][0][0]
            second_call_input = mock_build_prompt.call_args_list[1][0][0]

            assert first_call_input.market == "US"
            assert second_call_input.market == "KR"

    @pytest.mark.asyncio
    async def test_pipeline_extracts_valid_tickers_correctly(
        self,
        mock_ai_client,
        mock_log_repository,
        sample_ai_output
    ):
        """Test that pipeline correctly extracts tickers for validation."""
        # Setup input with specific tickers
        prompt_input = AIPromptInput(
            market="US",
            date="2024-01-01",
            filtered_stocks=[
                StockIndicators(
                    ticker="MSFT", name="Microsoft", market="US", close=300.0,
                    volume_ratio=1.1, rsi_14=58.0, ma_20=295.0, ma_60=290.0, atr_14=5.0
                ),
                StockIndicators(
                    ticker="TSLA", name="Tesla", market="US", close=800.0,
                    volume_ratio=2.0, rsi_14=75.0, ma_20=780.0, ma_60=760.0, atr_14=20.0
                )
            ],
            held_positions=[]
        )

        # Setup mocks
        mock_ai_client.call.return_value = sample_ai_output

        with patch('app.domain.ai.pipeline.build_prompt') as mock_build_prompt, \
             patch('app.domain.ai.pipeline.validate_ai_output_with_context') as mock_validate:

            mock_build_prompt.return_value = "test prompt"
            mock_validate.return_value = ValidationResult(is_valid=True, errors=[])

            # Create pipeline
            pipeline = AnalysisPipeline(mock_ai_client, mock_log_repository)

            # Test
            await pipeline.run(prompt_input, date(2024, 1, 1))

            # Verify validator called with correct tickers
            mock_validate.assert_called_once_with(sample_ai_output, ["MSFT", "TSLA"])
