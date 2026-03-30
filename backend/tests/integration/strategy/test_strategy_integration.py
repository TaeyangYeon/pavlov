"""
Integration tests for Strategy Integration Engine.
Tests the full pipeline: AI → Position Engine → Strategy Engine → Database.
"""

import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.domain.ai.schemas import AIPromptOutput, StockStrategy, TakeProfitLevel, StopLossLevel
from app.domain.position.schemas import PositionCreate, PositionEntry, TrailingStopConfig
from app.domain.strategy.change_detector import ChangeDetector
from app.domain.strategy.engine import StrategyIntegrationEngine
from app.infra.db.repositories.strategy_output_repository import StrategyOutputRepository
from app.infra.db.repositories.position_repository import PositionRepository
from app.infra.db.repositories.analysis_log_repository import AnalysisLogRepository
from app.domain.position.service import PositionService


@pytest.mark.asyncio
class TestStrategyIntegration:
    """Full integration tests for strategy system."""

    @pytest.fixture
    async def position_service(self, db_session):
        """Create PositionService with real repository."""
        repository = PositionRepository(db_session)
        return PositionService(repository)

    @pytest.fixture  
    async def strategy_repository(self, db_session):
        """Create StrategyOutputRepository."""
        return StrategyOutputRepository(db_session)

    @pytest.fixture
    async def analysis_log_repository(self, db_session):
        """Create AnalysisLogRepository."""
        return AnalysisLogRepository(db_session)

    @pytest.fixture
    async def change_detector(self):
        """Create ChangeDetector."""
        return ChangeDetector()

    @pytest.fixture
    async def strategy_engine(self, position_service, strategy_repository, change_detector):
        """Create StrategyIntegrationEngine with all dependencies."""
        return StrategyIntegrationEngine(
            position_service, strategy_repository, change_detector
        )

    @pytest.fixture
    async def sample_position(self, position_service):
        """Create a sample position for testing."""
        position_data = PositionCreate(
            ticker="AAPL",
            entries=[
                PositionEntry(
                    price=Decimal("150.00"),
                    quantity=Decimal("10.0000")
                )
            ]
        )
        return await position_service.create_position(position_data)

    async def test_strategy_engine_with_ai_only(
        self, 
        strategy_engine: StrategyIntegrationEngine,
        analysis_log_repository: AnalysisLogRepository
    ):
        """Test strategy engine with AI output but no positions."""
        # Create analysis log
        log = await analysis_log_repository.create("KR", date.today())
        
        # Mock AI output
        ai_output = AIPromptOutput(
            strategies=[
                StockStrategy(
                    ticker="TSLA",
                    action="buy",
                    rationale="Strong technical indicators",
                    confidence=0.85,
                    take_profit=[
                        TakeProfitLevel(pct=Decimal("10"), sell_ratio=Decimal("0.5"))
                    ],
                    stop_loss=[
                        StopLossLevel(pct=Decimal("-5"), sell_ratio=Decimal("1.0"))
                    ]
                )
            ]
        )

        # Run strategy integration
        result = await strategy_engine.run(
            market="KR",
            run_date=date.today(),
            ai_output=ai_output,
            analysis_log_id=log.id,
            trailing_configs=None
        )

        # Verify results
        assert result.market == "KR"
        assert result.total_tickers_analyzed == 1
        assert result.changed_count == 1  # First time, so changed
        assert len(result.strategies) == 1

        strategy = result.strategies[0]
        assert strategy.ticker == "TSLA"
        assert strategy.final_action == "buy"
        assert strategy.action_source == "ai"
        assert strategy.confidence == Decimal("0.85")
        assert strategy.changed_from_last is True

    async def test_strategy_engine_with_position_only(
        self, 
        strategy_engine: StrategyIntegrationEngine,
        analysis_log_repository: AnalysisLogRepository,
        sample_position
    ):
        """Test strategy engine with position but no AI output."""
        # Create analysis log
        log = await analysis_log_repository.create("US", date.today())
        
        # Run strategy integration with no AI output
        result = await strategy_engine.run(
            market="US",
            run_date=date.today(),
            ai_output=None,
            analysis_log_id=log.id,
            trailing_configs=None
        )

        # Verify results
        assert result.market == "US"
        assert result.total_tickers_analyzed == 1
        assert result.changed_count == 1  # First time, so changed
        assert len(result.strategies) == 1

        strategy = result.strategies[0]
        assert strategy.ticker == "AAPL"
        assert strategy.final_action == "hold"  # No AI, no triggers
        assert strategy.action_source == "merged"
        assert strategy.confidence == Decimal("1.0")  # Deterministic rule
        assert strategy.changed_from_last is True

    async def test_strategy_engine_ai_with_position_merge(
        self, 
        strategy_engine: StrategyIntegrationEngine,
        analysis_log_repository: AnalysisLogRepository,
        sample_position
    ):
        """Test strategy engine merging AI output with position data."""
        # Create analysis log
        log = await analysis_log_repository.create("US", date.today())
        
        # Mock AI output for same ticker as position
        ai_output = AIPromptOutput(
            strategies=[
                StockStrategy(
                    ticker="AAPL",
                    action="partial_sell",
                    rationale="Take some profits",
                    confidence=0.75,
                    take_profit=[
                        TakeProfitLevel(pct=Decimal("5"), sell_ratio=Decimal("0.3"))
                    ],
                    stop_loss=[]
                )
            ]
        )

        # Run strategy integration
        result = await strategy_engine.run(
            market="US",
            run_date=date.today(),
            ai_output=ai_output,
            analysis_log_id=log.id,
            trailing_configs=None
        )

        # Verify results
        assert result.market == "US"
        assert result.total_tickers_analyzed == 1
        assert result.changed_count == 1
        assert len(result.strategies) == 1

        strategy = result.strategies[0]
        assert strategy.ticker == "AAPL"
        assert strategy.final_action == "partial_sell"  # AI recommendation
        assert strategy.action_source == "ai"  # No position engine trigger
        assert strategy.confidence == Decimal("0.75")
        assert "Take some profits" in strategy.rationale
        assert strategy.changed_from_last is True

    async def test_strategy_engine_with_trailing_stop(
        self, 
        strategy_engine: StrategyIntegrationEngine,
        analysis_log_repository: AnalysisLogRepository,
        sample_position
    ):
        """Test strategy engine with trailing stop configuration."""
        # Create analysis log
        log = await analysis_log_repository.create("US", date.today())
        
        # Configure trailing stop
        trailing_configs = {
            "AAPL": TrailingStopConfig(
                mode="percentage",
                trail_pct=Decimal("10.0")
            )
        }

        # Mock AI output
        ai_output = AIPromptOutput(
            strategies=[
                StockStrategy(
                    ticker="AAPL",
                    action="hold",
                    rationale="Wait and see",
                    confidence=0.6,
                    take_profit=[],
                    stop_loss=[]
                )
            ]
        )

        # Run strategy integration
        result = await strategy_engine.run(
            market="US",
            run_date=date.today(),
            ai_output=ai_output,
            analysis_log_id=log.id,
            trailing_configs=trailing_configs
        )

        # Verify results
        assert result.market == "US"
        assert result.total_tickers_analyzed == 1
        assert len(result.strategies) == 1

        strategy = result.strategies[0]
        assert strategy.ticker == "AAPL"
        # Should be either hold or trailing stop action depending on evaluation
        assert strategy.final_action in ["hold", "full_exit"]
        assert strategy.changed_from_last is True

    async def test_change_detection_no_change(
        self, 
        strategy_engine: StrategyIntegrationEngine,
        analysis_log_repository: AnalysisLogRepository,
        sample_position
    ):
        """Test that unchanged strategies are not saved twice."""
        # Create analysis log
        log1 = await analysis_log_repository.create("US", date.today())
        
        # Same AI output
        ai_output = AIPromptOutput(
            strategies=[
                StockStrategy(
                    ticker="AAPL",
                    action="hold",
                    rationale="No change",
                    confidence=0.5,
                    take_profit=[],
                    stop_loss=[]
                )
            ]
        )

        # Run first time
        result1 = await strategy_engine.run(
            market="US",
            run_date=date.today(),
            ai_output=ai_output,
            analysis_log_id=log1.id,
            trailing_configs=None
        )

        assert result1.changed_count == 1  # First time = changed

        # Run second time with same output
        log2 = await analysis_log_repository.create("US", date.today())
        result2 = await strategy_engine.run(
            market="US",
            run_date=date.today(),
            ai_output=ai_output,
            analysis_log_id=log2.id,
            trailing_configs=None
        )

        # Should detect no change
        assert result2.changed_count == 0  # No change detected
        strategy = result2.strategies[0]
        assert strategy.changed_from_last is False

    async def test_multiple_tickers_mixed_sources(
        self, 
        strategy_engine: StrategyIntegrationEngine,
        analysis_log_repository: AnalysisLogRepository,
        sample_position,
        position_service: PositionService
    ):
        """Test with multiple tickers from different sources."""
        # Create second position
        position_data = PositionCreate(
            ticker="GOOGL",
            entries=[
                PositionEntry(
                    price=Decimal("2800.00"),
                    quantity=Decimal("2.0000")
                )
            ]
        )
        await position_service.create_position(position_data)

        # Create analysis log
        log = await analysis_log_repository.create("US", date.today())
        
        # AI output for only one ticker + new ticker
        ai_output = AIPromptOutput(
            strategies=[
                StockStrategy(
                    ticker="AAPL",  # Has position
                    action="buy", 
                    rationale="Buy more",
                    confidence=0.8,
                    take_profit=[],
                    stop_loss=[]
                ),
                StockStrategy(
                    ticker="NVDA",  # No position
                    action="buy",
                    rationale="New opportunity", 
                    confidence=0.9,
                    take_profit=[],
                    stop_loss=[]
                )
            ]
        )

        # Run strategy integration
        result = await strategy_engine.run(
            market="US",
            run_date=date.today(),
            ai_output=ai_output,
            analysis_log_id=log.id,
            trailing_configs=None
        )

        # Should have 3 strategies: AAPL (AI+pos), GOOGL (pos only), NVDA (AI only)
        assert result.total_tickers_analyzed == 3
        assert result.changed_count == 3  # All new
        assert len(result.strategies) == 3

        tickers = {s.ticker for s in result.strategies}
        assert tickers == {"AAPL", "GOOGL", "NVDA"}

        # Verify sources
        for strategy in result.strategies:
            if strategy.ticker == "AAPL":
                assert strategy.action_source == "ai"  # AI recommendation
            elif strategy.ticker == "GOOGL": 
                assert strategy.action_source == "merged"  # Position only
            elif strategy.ticker == "NVDA":
                assert strategy.action_source == "ai"  # AI only

    async def test_error_handling_invalid_position(
        self, 
        strategy_engine: StrategyIntegrationEngine,
        analysis_log_repository: AnalysisLogRepository
    ):
        """Test error handling with invalid position data."""
        # Create analysis log
        log = await analysis_log_repository.create("KR", date.today())
        
        # This should not raise an exception even with no positions or AI data
        result = await strategy_engine.run(
            market="KR",
            run_date=date.today(),
            ai_output=None,
            analysis_log_id=log.id,
            trailing_configs=None
        )

        # Should handle gracefully
        assert result.market == "KR"
        assert result.total_tickers_analyzed == 0
        assert result.changed_count == 0
        assert len(result.strategies) == 0