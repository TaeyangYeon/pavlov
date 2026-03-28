"""Integration tests for AnalysisPipeline with real database and dependencies."""
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from app.core.container import get_container
from app.domain.ai.schemas import (
    AIPromptInput,
    AIPromptOutput,
    StockIndicators,
    StockStrategy,
    StopLossLevel,
    TakeProfitLevel,
)
from app.infra.db.models.analysis_log import AnalysisLog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class TestAnalysisPipelineIntegration:
    """Integration tests for the complete AnalysisPipeline."""

    @pytest.fixture
    def sample_prompt_input(self):
        """Sample prompt input with filtered stocks for testing."""
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
    def valid_ai_output(self):
        """Valid AI output that will pass validation."""
        return AIPromptOutput(
            market_summary="Market looking bullish with good momentum",
            strategies=[
                StockStrategy(
                    ticker="AAPL",
                    action="buy",
                    take_profit=[TakeProfitLevel(pct=10.0, sell_ratio=0.5)],
                    stop_loss=[StopLossLevel(pct=-5.0, sell_ratio=1.0)],
                    rationale="Strong technical setup",
                    confidence=0.8
                ),
                StockStrategy(
                    ticker="GOOGL",
                    action="hold",
                    take_profit=[],
                    stop_loss=[StopLossLevel(pct=-3.0, sell_ratio=1.0)],
                    rationale="Consolidation phase",
                    confidence=0.6
                )
            ]
        )

    @pytest.fixture
    def invalid_ai_output(self):
        """Invalid AI output with hallucinated ticker."""
        return AIPromptOutput(
            market_summary="Market analysis with invalid ticker",
            strategies=[
                StockStrategy(
                    ticker="FAKE_TICKER",  # Hallucination
                    action="buy",
                    take_profit=[TakeProfitLevel(pct=15.0, sell_ratio=0.7)],
                    stop_loss=[StopLossLevel(pct=-8.0, sell_ratio=1.0)],
                    rationale="Hallucinated strategy",
                    confidence=0.9
                )
            ]
        )

    @pytest.mark.asyncio
    async def test_pipeline_end_to_end_success(
        self,
        db_session: AsyncSession,
        sample_prompt_input,
        valid_ai_output
    ):
        """Test complete pipeline with real database - success case."""
        # Setup
        container = get_container()

        # Mock AI client to return valid output
        with patch.object(container, 'ai_client') as mock_ai_client_factory:
            mock_ai_client = AsyncMock()
            mock_ai_client.call.return_value = valid_ai_output
            mock_ai_client_factory.return_value = mock_ai_client

            # Create pipeline through container
            pipeline = container.analysis_pipeline(db_session)

            # Test
            result = await pipeline.run(sample_prompt_input, date(2024, 1, 1))

            # Verify result
            assert result is not None
            assert isinstance(result, AIPromptOutput)
            assert result == valid_ai_output

            # Verify database log was saved with executed=True
            stmt = select(AnalysisLog).where(
                AnalysisLog.market == "US",
                AnalysisLog.date == date(2024, 1, 1),
                AnalysisLog.executed == True  # noqa: E712
            )
            db_result = await db_session.execute(stmt)
            log_entry = db_result.scalar_one_or_none()

            assert log_entry is not None
            assert log_entry.executed is True
            assert log_entry.ai_response is not None
            assert log_entry.ai_response["market_summary"] == "Market looking bullish with good momentum"
            assert len(log_entry.ai_response["strategies"]) == 2
            assert log_entry.error_message is None

    @pytest.mark.asyncio
    async def test_pipeline_end_to_end_validation_failure(
        self,
        db_session: AsyncSession,
        sample_prompt_input,
        invalid_ai_output
    ):
        """Test complete pipeline with validation failure."""
        # Setup
        container = get_container()

        # Mock AI client to return invalid output
        with patch.object(container, 'ai_client') as mock_ai_client_factory:
            mock_ai_client = AsyncMock()
            mock_ai_client.call.return_value = invalid_ai_output
            mock_ai_client_factory.return_value = mock_ai_client

            # Create pipeline through container
            pipeline = container.analysis_pipeline(db_session)

            # Test
            result = await pipeline.run(sample_prompt_input, date(2024, 1, 1))

            # Verify result
            assert result is None  # Validation failed

            # Verify database log was saved with executed=False
            stmt = select(AnalysisLog).where(
                AnalysisLog.market == "US",
                AnalysisLog.date == date(2024, 1, 1),
                AnalysisLog.executed == False  # noqa: E712
            )
            db_result = await db_session.execute(stmt)
            log_entry = db_result.scalar_one_or_none()

            assert log_entry is not None
            assert log_entry.executed is False
            assert log_entry.ai_response is None
            assert log_entry.error_message is not None
            assert "FAKE_TICKER" in log_entry.error_message
            assert "not in filtered stocks" in log_entry.error_message
            assert "hallucination" in log_entry.error_message

    @pytest.mark.asyncio
    async def test_pipeline_container_dependency_injection(
        self,
        db_session: AsyncSession
    ):
        """Test that container properly injects dependencies."""
        # Setup
        container = get_container()

        # Test
        pipeline = container.analysis_pipeline(db_session)

        # Verify
        assert pipeline is not None
        assert hasattr(pipeline, '_ai_client')
        assert hasattr(pipeline, '_analysis_log_repository')

        # Verify dependencies are properly injected
        ai_client = pipeline._ai_client
        log_repository = pipeline._analysis_log_repository

        assert ai_client is not None
        assert log_repository is not None
        assert log_repository._session == db_session

    @pytest.mark.asyncio
    async def test_pipeline_prompt_builder_integration(
        self,
        db_session: AsyncSession,
        sample_prompt_input,
        valid_ai_output
    ):
        """Test that pipeline correctly integrates with prompt builder."""
        # Setup
        container = get_container()

        # Mock AI client
        with patch.object(container, 'ai_client') as mock_ai_client_factory:
            mock_ai_client = AsyncMock()
            mock_ai_client.call.return_value = valid_ai_output
            mock_ai_client_factory.return_value = mock_ai_client

            # Patch prompt builder to verify it's called
            with patch('app.domain.ai.pipeline.build_prompt') as mock_build_prompt:
                mock_build_prompt.return_value = "test prompt"

                # Create pipeline and run
                pipeline = container.analysis_pipeline(db_session)
                result = await pipeline.run(sample_prompt_input, date(2024, 1, 1))

                # Verify prompt builder was called
                mock_build_prompt.assert_called_once_with(sample_prompt_input)

                # Verify AI client was called with prompt
                mock_ai_client.call.assert_called_once_with("test prompt")

                # Verify result
                assert result == valid_ai_output

    @pytest.mark.asyncio
    async def test_pipeline_validation_integration(
        self,
        db_session: AsyncSession,
        sample_prompt_input,
        valid_ai_output
    ):
        """Test that pipeline correctly integrates with enhanced validation."""
        # Setup
        container = get_container()

        # Mock AI client
        with patch.object(container, 'ai_client') as mock_ai_client_factory:
            mock_ai_client = AsyncMock()
            mock_ai_client.call.return_value = valid_ai_output
            mock_ai_client_factory.return_value = mock_ai_client

            # Patch validator to verify it's called correctly
            with patch('app.domain.ai.pipeline.validate_ai_output_with_context') as mock_validate:
                from app.domain.ai.schemas import ValidationResult
                mock_validate.return_value = ValidationResult(is_valid=True, errors=[])

                # Create pipeline and run
                pipeline = container.analysis_pipeline(db_session)
                result = await pipeline.run(sample_prompt_input, date(2024, 1, 1))

                # Verify validator was called with correct parameters
                mock_validate.assert_called_once_with(valid_ai_output, ["AAPL", "GOOGL"])

                # Verify result
                assert result == valid_ai_output

    @pytest.mark.asyncio
    async def test_pipeline_analysis_log_persistence_success(
        self,
        db_session: AsyncSession,
        sample_prompt_input,
        valid_ai_output
    ):
        """Test that pipeline correctly persists analysis logs on success."""
        # Setup
        container = get_container()
        analysis_date = date(2024, 1, 15)

        # Mock AI client
        with patch.object(container, 'ai_client') as mock_ai_client_factory:
            mock_ai_client = AsyncMock()
            mock_ai_client.call.return_value = valid_ai_output
            mock_ai_client_factory.return_value = mock_ai_client

            # Create pipeline and run
            pipeline = container.analysis_pipeline(db_session)
            result = await pipeline.run(sample_prompt_input, analysis_date)

            # Verify result
            assert result == valid_ai_output

            # Check analysis log details
            stmt = select(AnalysisLog).where(
                AnalysisLog.market == "US",
                AnalysisLog.date == analysis_date
            )
            db_result = await db_session.execute(stmt)
            log_entry = db_result.scalar_one_or_none()

            assert log_entry is not None
            assert log_entry.market == "US"
            assert log_entry.date == analysis_date
            assert log_entry.executed is True
            assert log_entry.ai_response == valid_ai_output.model_dump()
            assert log_entry.error_message is None
            assert log_entry.created_at is not None
            assert log_entry.updated_at is not None

    @pytest.mark.asyncio
    async def test_pipeline_analysis_log_persistence_failure(
        self,
        db_session: AsyncSession,
        sample_prompt_input,
        invalid_ai_output
    ):
        """Test that pipeline correctly persists analysis logs on validation failure."""
        # Setup
        container = get_container()
        analysis_date = date(2024, 1, 16)

        # Mock AI client
        with patch.object(container, 'ai_client') as mock_ai_client_factory:
            mock_ai_client = AsyncMock()
            mock_ai_client.call.return_value = invalid_ai_output
            mock_ai_client_factory.return_value = mock_ai_client

            # Create pipeline and run
            pipeline = container.analysis_pipeline(db_session)
            result = await pipeline.run(sample_prompt_input, analysis_date)

            # Verify result
            assert result is None

            # Check analysis log details
            stmt = select(AnalysisLog).where(
                AnalysisLog.market == "US",
                AnalysisLog.date == analysis_date
            )
            db_result = await db_session.execute(stmt)
            log_entry = db_result.scalar_one_or_none()

            assert log_entry is not None
            assert log_entry.market == "US"
            assert log_entry.date == analysis_date
            assert log_entry.executed is False
            assert log_entry.ai_response is None
            assert log_entry.error_message is not None
            assert "Validation failed" in log_entry.error_message
            assert log_entry.created_at is not None
            assert log_entry.updated_at is not None
