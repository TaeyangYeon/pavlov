"""
Unit tests for StrategyIntegrationEngine (TDD - Red Phase).
All tests should FAIL before implementation.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest

from app.domain.ai.schemas import AIPromptOutput, StockStrategy, TakeProfitLevel, StopLossLevel
from app.domain.position.schemas import (
    PositionResponse,
    PositionEntry,
    TpSlEvaluationResponse,
    TrailingStopEvaluationResponse,
)
from app.domain.strategy.engine import StrategyIntegrationEngine
from app.domain.strategy.schemas import UnifiedStrategy, StrategyRunResult


class TestStrategyIntegrationEngine:
    """Test suite for StrategyIntegrationEngine."""

    def setup_method(self):
        """Setup test dependencies."""
        self.position_service = AsyncMock()
        self.strategy_repository = AsyncMock()
        self.change_detector = Mock()
        
        self.engine = StrategyIntegrationEngine(
            position_service=self.position_service,
            strategy_repository=self.strategy_repository,
            change_detector=self.change_detector,
        )

    # ── MERGE LOGIC TESTS ──

    def test_ai_buy_no_position_returns_buy(self):
        """AI says buy, no open position → final action = buy"""
        ai_strategy = StockStrategy(
            ticker="AAPL",
            action="buy",
            take_profit=[TakeProfitLevel(pct=10.0, sell_ratio=0.5)],
            stop_loss=[StopLossLevel(pct=-5.0, sell_ratio=1.0)],
            rationale="Strong buy signal",
            confidence=0.8
        )
        
        # No position engine results (no position)
        unified = self.engine._merge(
            ticker="AAPL",
            market="US",
            ai_strategy=ai_strategy,
            tp_sl_result=None,
            trailing_result=None,
        )
        
        assert unified.final_action == "buy"
        assert unified.action_source == "ai"
        assert unified.confidence == Decimal("0.8")
        assert unified.sell_quantity == Decimal("0.0000")

    def test_ai_hold_position_engine_partial_sell(self):
        """AI says hold, position engine says partial_sell → final = partial_sell"""
        ai_strategy = StockStrategy(
            ticker="AAPL",
            action="hold",
            take_profit=[],
            stop_loss=[],
            rationale="Market uncertain",
            confidence=0.6
        )
        
        tp_sl_result = TpSlEvaluationResponse(
            position_id=uuid4(),
            ticker="AAPL",
            action="partial_sell",
            triggered_by="tp",
            triggered_level_pct=Decimal("10.0"),
            sell_quantity=Decimal("5.0"),
            sell_ratio=Decimal("0.5"),
            current_pnl_pct=Decimal("12.0"),
            realized_pnl_estimate=Decimal("100.0"),
            avg_price=Decimal("100.0"),
            current_price=Decimal("112.0"),
            total_quantity=Decimal("10.0")
        )
        
        unified = self.engine._merge(
            ticker="AAPL",
            market="US",
            ai_strategy=ai_strategy,
            tp_sl_result=tp_sl_result,
            trailing_result=None,
        )
        
        assert unified.final_action == "partial_sell"
        assert unified.action_source == "position_engine"
        assert unified.sell_quantity == Decimal("5.0")
        assert "TP triggered at 10.0%" in unified.rationale

    def test_ai_partial_sell_engine_full_exit(self):
        """AI says partial_sell, position engine says full_exit → final = full_exit (more severe wins)"""
        ai_strategy = StockStrategy(
            ticker="AAPL",
            action="partial_sell",
            take_profit=[],
            stop_loss=[],
            rationale="Reduce exposure",
            confidence=0.7
        )
        
        trailing_result = TrailingStopEvaluationResponse(
            position_id=uuid4(),
            ticker="AAPL",
            triggered=True,
            action="full_exit",
            high_water_mark=Decimal("130.0"),
            stop_price=Decimal("117.0"),
            current_price=Decimal("116.0"),
            trail_distance_pct=Decimal("10.0"),
            distance_to_stop_pct=Decimal("-0.9"),
            new_high_water_mark=Decimal("130.0"),
            hwm_updated=False
        )
        
        unified = self.engine._merge(
            ticker="AAPL",
            market="US",
            ai_strategy=ai_strategy,
            tp_sl_result=None,
            trailing_result=trailing_result,
        )
        
        assert unified.final_action == "full_exit"
        assert unified.action_source == "position_engine"
        assert "Trailing stop triggered" in unified.rationale

    def test_ai_full_exit_engine_hold(self):
        """AI says full_exit, position engine says hold → final = full_exit (AI respected)"""
        ai_strategy = StockStrategy(
            ticker="AAPL",
            action="full_exit",
            take_profit=[],
            stop_loss=[],
            rationale="Exit signal",
            confidence=0.9
        )
        
        tp_sl_result = TpSlEvaluationResponse(
            position_id=uuid4(),
            ticker="AAPL",
            action="hold",
            triggered_by="none",
            triggered_level_pct=None,
            sell_quantity=Decimal("0.0"),
            sell_ratio=Decimal("0.0"),
            current_pnl_pct=Decimal("5.0"),
            realized_pnl_estimate=Decimal("0.0"),
            avg_price=Decimal("100.0"),
            current_price=Decimal("105.0"),
            total_quantity=Decimal("10.0")
        )
        
        unified = self.engine._merge(
            ticker="AAPL",
            market="US",
            ai_strategy=ai_strategy,
            tp_sl_result=tp_sl_result,
            trailing_result=None,
        )
        
        assert unified.final_action == "full_exit"
        assert unified.action_source == "ai"
        assert unified.confidence == Decimal("0.9")

    def test_ai_hold_engine_hold_returns_hold(self):
        """Both say hold → final = hold"""
        ai_strategy = StockStrategy(
            ticker="AAPL",
            action="hold",
            take_profit=[],
            stop_loss=[],
            rationale="No signal",
            confidence=0.5
        )
        
        tp_sl_result = TpSlEvaluationResponse(
            position_id=uuid4(),
            ticker="AAPL",
            action="hold",
            triggered_by="none",
            triggered_level_pct=None,
            sell_quantity=Decimal("0.0"),
            sell_ratio=Decimal("0.0"),
            current_pnl_pct=Decimal("2.0"),
            realized_pnl_estimate=Decimal("0.0"),
            avg_price=Decimal("100.0"),
            current_price=Decimal("102.0"),
            total_quantity=Decimal("10.0")
        )
        
        unified = self.engine._merge(
            ticker="AAPL",
            market="US",
            ai_strategy=ai_strategy,
            tp_sl_result=tp_sl_result,
            trailing_result=None,
        )
        
        assert unified.final_action == "hold"
        assert unified.action_source == "merged"

    async def test_position_only_not_in_ai_output(self):
        """Open position ticker not in AI output → include with source=position_engine"""
        # Mock open positions
        position = PositionResponse(
            id=uuid4(),
            ticker="MSFT",
            market="US",
            entries=[PositionEntry(
                price=Decimal("200.0"),
                quantity=Decimal("5.0"),
                entered_at="2023-01-01T00:00:00"
            )],
            avg_price=Decimal("200.0"),
            status="open",
            created_at="2023-01-01T00:00:00",
            updated_at="2023-01-01T00:00:00"
        )
        
        self.position_service.get_open_positions.return_value = [position]
        self.position_service.evaluate_tp_sl.return_value = TpSlEvaluationResponse(
            position_id=position.id,
            ticker="MSFT",
            action="partial_sell",
            triggered_by="tp",
            triggered_level_pct=Decimal("15.0"),
            sell_quantity=Decimal("2.0"),
            sell_ratio=Decimal("0.4"),
            current_pnl_pct=Decimal("15.0"),
            realized_pnl_estimate=Decimal("150.0"),
            avg_price=Decimal("200.0"),
            current_price=Decimal("230.0"),
            total_quantity=Decimal("5.0")
        )
        
        self.change_detector.has_changed.return_value = True
        
        # AI output without MSFT
        ai_output = AIPromptOutput(
            market_summary="No MSFT signal",
            strategies=[]
        )
        
        result = await self.engine.run(
            market="US",
            run_date=date.today(),
            ai_output=ai_output,
            analysis_log_id=uuid4(),
        )
        
        # Should include MSFT with position_engine source
        msft_strategy = next((s for s in result.strategies if s.ticker == "MSFT"), None)
        assert msft_strategy is not None
        assert msft_strategy.action_source == "position_engine"
        assert msft_strategy.final_action == "partial_sell"

    def test_confidence_uses_ai_value(self):
        """AI confidence should be preserved"""
        ai_strategy = StockStrategy(
            ticker="AAPL",
            action="buy",
            take_profit=[],
            stop_loss=[],
            rationale="Strong signal",
            confidence=0.75
        )
        
        unified = self.engine._merge(
            ticker="AAPL",
            market="US",
            ai_strategy=ai_strategy,
            tp_sl_result=None,
            trailing_result=None,
        )
        
        assert unified.confidence == Decimal("0.75")

    def test_confidence_is_one_for_position_only(self):
        """No AI strategy → confidence = 1.0 (deterministic)"""
        tp_sl_result = TpSlEvaluationResponse(
            position_id=uuid4(),
            ticker="AAPL",
            action="partial_sell",
            triggered_by="sl",
            triggered_level_pct=Decimal("-10.0"),
            sell_quantity=Decimal("10.0"),
            sell_ratio=Decimal("1.0"),
            current_pnl_pct=Decimal("-12.0"),
            realized_pnl_estimate=Decimal("-120.0"),
            avg_price=Decimal("100.0"),
            current_price=Decimal("88.0"),
            total_quantity=Decimal("10.0")
        )
        
        unified = self.engine._merge(
            ticker="AAPL",
            market="US",
            ai_strategy=None,
            tp_sl_result=tp_sl_result,
            trailing_result=None,
        )
        
        assert unified.confidence == Decimal("1.0")

    def test_rationale_merged_correctly(self):
        """AI + engine rationale should be combined"""
        ai_strategy = StockStrategy(
            ticker="AAPL",
            action="hold",
            take_profit=[],
            stop_loss=[],
            rationale="강세 신호",
            confidence=0.6
        )
        
        tp_sl_result = TpSlEvaluationResponse(
            position_id=uuid4(),
            ticker="AAPL",
            action="partial_sell",
            triggered_by="tp",
            triggered_level_pct=Decimal("10.0"),
            sell_quantity=Decimal("5.0"),
            sell_ratio=Decimal("0.5"),
            current_pnl_pct=Decimal("12.0"),
            realized_pnl_estimate=Decimal("100.0"),
            avg_price=Decimal("100.0"),
            current_price=Decimal("112.0"),
            total_quantity=Decimal("10.0")
        )
        
        unified = self.engine._merge(
            ticker="AAPL",
            market="US",
            ai_strategy=ai_strategy,
            tp_sl_result=tp_sl_result,
            trailing_result=None,
        )
        
        assert "강세 신호" in unified.rationale
        assert "TP triggered at 10.0%" in unified.rationale
        assert " | " in unified.rationale

    def test_rationale_max_200_chars(self):
        """Very long rationale should be truncated to 200 chars"""
        ai_strategy = StockStrategy(
            ticker="AAPL",
            action="buy",
            take_profit=[],
            stop_loss=[],
            rationale="A" * 150,  # 150 chars
            confidence=0.8
        )
        
        tp_sl_result = TpSlEvaluationResponse(
            position_id=uuid4(),
            ticker="AAPL",
            action="hold",
            triggered_by="none",
            triggered_level_pct=None,
            sell_quantity=Decimal("0.0"),
            sell_ratio=Decimal("0.0"),
            current_pnl_pct=Decimal("5.0"),
            realized_pnl_estimate=Decimal("0.0"),
            avg_price=Decimal("100.0"),
            current_price=Decimal("105.0"),
            total_quantity=Decimal("10.0")
        )
        
        unified = self.engine._merge(
            ticker="AAPL",
            market="US",
            ai_strategy=ai_strategy,
            tp_sl_result=tp_sl_result,
            trailing_result=None,
        )
        
        assert len(unified.rationale) <= 200

    # ── SELL QUANTITY TESTS ──

    def test_sell_quantity_from_position_engine(self):
        """Sell quantity should come from position engine"""
        tp_sl_result = TpSlEvaluationResponse(
            position_id=uuid4(),
            ticker="AAPL",
            action="partial_sell",
            triggered_by="tp",
            triggered_level_pct=Decimal("20.0"),
            sell_quantity=Decimal("7.5"),
            sell_ratio=Decimal("0.75"),
            current_pnl_pct=Decimal("25.0"),
            realized_pnl_estimate=Decimal("250.0"),
            avg_price=Decimal("100.0"),
            current_price=Decimal("125.0"),
            total_quantity=Decimal("10.0")
        )
        
        unified = self.engine._merge(
            ticker="AAPL",
            market="US",
            ai_strategy=None,
            tp_sl_result=tp_sl_result,
            trailing_result=None,
        )
        
        assert unified.sell_quantity == Decimal("7.5")
        assert unified.realized_pnl_estimate == Decimal("250.0")

    def test_sell_quantity_zero_on_hold(self):
        """Hold action should have zero sell quantity"""
        ai_strategy = StockStrategy(
            ticker="AAPL",
            action="hold",
            take_profit=[],
            stop_loss=[],
            rationale="Wait and see",
            confidence=0.5
        )
        
        unified = self.engine._merge(
            ticker="AAPL",
            market="US",
            ai_strategy=ai_strategy,
            tp_sl_result=None,
            trailing_result=None,
        )
        
        assert unified.final_action == "hold"
        assert unified.sell_quantity == Decimal("0.0000")

    def test_sell_quantity_zero_on_buy(self):
        """Buy action should have zero sell quantity"""
        ai_strategy = StockStrategy(
            ticker="AAPL",
            action="buy",
            take_profit=[],
            stop_loss=[],
            rationale="Buy signal",
            confidence=0.8
        )
        
        unified = self.engine._merge(
            ticker="AAPL",
            market="US",
            ai_strategy=ai_strategy,
            tp_sl_result=None,
            trailing_result=None,
        )
        
        assert unified.final_action == "buy"
        assert unified.sell_quantity == Decimal("0.0000")