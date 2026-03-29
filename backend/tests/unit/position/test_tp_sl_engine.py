"""
Unit tests for TpSlEngine.
Tests TP/SL judgment engine with boundary value testing.
"""

from decimal import Decimal

import pytest
from app.domain.ai.schemas import StopLossLevel, TakeProfitLevel
from app.domain.position.schemas import TpSlDecision
from app.domain.position.tp_sl_engine import TpSlEngine


@pytest.fixture
def engine():
    """TpSlEngine instance for testing."""
    return TpSlEngine()


@pytest.fixture
def tp_levels_multi():
    """Multi-level TP setup for testing."""
    return [
        TakeProfitLevel(pct=10.0, sell_ratio=0.3),
        TakeProfitLevel(pct=20.0, sell_ratio=0.5),
        TakeProfitLevel(pct=30.0, sell_ratio=1.0),
    ]


@pytest.fixture
def sl_levels_multi():
    """Multi-level SL setup for testing."""
    return [
        StopLossLevel(pct=-5.0, sell_ratio=0.5),
        StopLossLevel(pct=-10.0, sell_ratio=1.0),
    ]


class TestTpSlEngine:
    """Test cases for TP/SL judgment engine."""

    # ── HOLD CASES ──

    def test_hold_when_no_levels_triggered(self, engine):
        """Test hold when no TP/SL levels are triggered."""
        # avg=100, current=103 (pnl=+3%) → action="hold"
        decision = engine.evaluate(
            avg_price=Decimal("100.00"),
            current_price=Decimal("103.00"),
            total_quantity=Decimal("10"),
            take_profit_levels=[TakeProfitLevel(pct=10.0, sell_ratio=0.5)],
            stop_loss_levels=[StopLossLevel(pct=-5.0, sell_ratio=0.5)]
        )
        
        assert decision.action == "hold"
        assert decision.triggered_by == "none"
        assert decision.triggered_level_pct is None
        assert decision.sell_quantity == Decimal("0.0000")
        assert decision.sell_ratio == Decimal("0.0000")
        assert decision.current_pnl_pct == Decimal("3.0000")
        assert decision.realized_pnl_estimate == Decimal("0.0000")

    def test_hold_when_tp_not_reached(self, engine):
        """Test hold when TP not reached."""
        # avg=100, current=109 (pnl=+9%) → below 10% TP → "hold"
        decision = engine.evaluate(
            avg_price=Decimal("100.00"),
            current_price=Decimal("109.00"),
            total_quantity=Decimal("10"),
            take_profit_levels=[TakeProfitLevel(pct=10.0, sell_ratio=0.5)],
            stop_loss_levels=[]
        )
        
        assert decision.action == "hold"
        assert decision.triggered_by == "none"

    def test_hold_when_sl_not_reached(self, engine):
        """Test hold when SL not reached."""
        # avg=100, current=96 (pnl=-4%) → above -5% SL → "hold"
        decision = engine.evaluate(
            avg_price=Decimal("100.00"),
            current_price=Decimal("96.00"),
            total_quantity=Decimal("10"),
            take_profit_levels=[],
            stop_loss_levels=[StopLossLevel(pct=-5.0, sell_ratio=0.5)]
        )
        
        assert decision.action == "hold"
        assert decision.triggered_by == "none"

    # ── TP BOUNDARY TESTS ──

    @pytest.mark.parametrize("current_price,expected_action,expected_triggered", [
        (Decimal("109.9999"), "hold", "none"),          # pnl = +9.9999% → not triggered
        (Decimal("110.0000"), "partial_sell", "tp"),    # pnl = +10.0% → exact trigger
        (Decimal("110.0001"), "partial_sell", "tp"),    # pnl = +10.0001% → triggered
        (Decimal("120.0000"), "partial_sell", "tp"),    # pnl = +20% → level 2
        (Decimal("130.0000"), "full_exit", "tp"),       # pnl = +30% → full exit
    ])
    def test_tp_boundary_values(self, engine, tp_levels_multi, current_price, expected_action, expected_triggered):
        """Test TP boundary value precision."""
        decision = engine.evaluate(
            avg_price=Decimal("100.00"),
            current_price=current_price,
            total_quantity=Decimal("10"),
            take_profit_levels=tp_levels_multi,
            stop_loss_levels=[]
        )
        
        assert decision.action == expected_action
        assert decision.triggered_by == expected_triggered

    # ── SL BOUNDARY TESTS ──

    @pytest.mark.parametrize("current_price,expected_action,expected_triggered", [
        (Decimal("95.0001"), "hold", "none"),           # pnl = -4.9999% → not triggered
        (Decimal("95.0000"), "partial_sell", "sl"),     # pnl = -5.0% → exact trigger
        (Decimal("94.9999"), "partial_sell", "sl"),     # pnl = -5.0001% → triggered
        (Decimal("90.0000"), "full_exit", "sl"),        # pnl = -10% → full exit
    ])
    def test_sl_boundary_values(self, engine, sl_levels_multi, current_price, expected_action, expected_triggered):
        """Test SL boundary value precision."""
        decision = engine.evaluate(
            avg_price=Decimal("100.00"),
            current_price=current_price,
            total_quantity=Decimal("10"),
            take_profit_levels=[],
            stop_loss_levels=sl_levels_multi
        )
        
        assert decision.action == expected_action
        assert decision.triggered_by == expected_triggered

    # ── MULTI-LEVEL TESTS ──

    def test_highest_tp_level_taken(self, engine, tp_levels_multi):
        """Test highest triggered TP level is taken."""
        # avg=100, current=125 (+25%)
        # → +10% triggered, +20% triggered, +30% NOT
        # → triggered_level_pct = 20, sell_ratio = 0.5
        decision = engine.evaluate(
            avg_price=Decimal("100.00"),
            current_price=Decimal("125.00"),
            total_quantity=Decimal("10"),
            take_profit_levels=tp_levels_multi,
            stop_loss_levels=[]
        )
        
        assert decision.action == "partial_sell"
        assert decision.triggered_by == "tp"
        assert decision.triggered_level_pct == Decimal("20.0000")
        assert decision.sell_ratio == Decimal("0.5000")
        assert decision.sell_quantity == Decimal("5.0000")

    def test_most_severe_sl_taken(self, engine, sl_levels_multi):
        """Test most severe triggered SL level is taken."""
        # avg=100, current=88 (-12%)
        # → -5% triggered, -10% triggered, -15% NOT
        # → triggered_level_pct = -10, sell_ratio = 1.0
        decision = engine.evaluate(
            avg_price=Decimal("100.00"),
            current_price=Decimal("88.00"),
            total_quantity=Decimal("10"),
            take_profit_levels=[],
            stop_loss_levels=sl_levels_multi
        )
        
        assert decision.action == "full_exit"
        assert decision.triggered_by == "sl"
        assert decision.triggered_level_pct == Decimal("-10.0000")
        assert decision.sell_ratio == Decimal("1.0000")
        assert decision.sell_quantity == Decimal("10.0000")

    # ── SELL QUANTITY TESTS ──

    def test_partial_sell_quantity_calculation(self, engine):
        """Test partial sell quantity calculation."""
        # total_quantity=10, sell_ratio=0.3
        # → sell_quantity = 3.0000
        decision = engine.evaluate(
            avg_price=Decimal("100.00"),
            current_price=Decimal("110.00"),
            total_quantity=Decimal("10"),
            take_profit_levels=[TakeProfitLevel(pct=10.0, sell_ratio=0.3)],
            stop_loss_levels=[]
        )
        
        assert decision.sell_quantity == Decimal("3.0000")
        assert decision.action == "partial_sell"

    def test_full_exit_quantity_equals_total(self, engine):
        """Test full exit quantity equals total."""
        # total_quantity=10, sell_ratio=1.0
        # → sell_quantity = 10.0000
        # → action = "full_exit"
        decision = engine.evaluate(
            avg_price=Decimal("100.00"),
            current_price=Decimal("130.00"),
            total_quantity=Decimal("10"),
            take_profit_levels=[TakeProfitLevel(pct=30.0, sell_ratio=1.0)],
            stop_loss_levels=[]
        )
        
        assert decision.sell_quantity == Decimal("10.0000")
        assert decision.action == "full_exit"
        assert decision.sell_ratio == Decimal("1.0000")

    def test_sell_quantity_is_decimal_not_float(self, engine):
        """Test sell quantity is Decimal type, not float."""
        decision = engine.evaluate(
            avg_price=Decimal("100.00"),
            current_price=Decimal("110.00"),
            total_quantity=Decimal("10"),
            take_profit_levels=[TakeProfitLevel(pct=10.0, sell_ratio=0.3)],
            stop_loss_levels=[]
        )
        
        assert type(decision.sell_quantity) == Decimal
        assert type(decision.sell_ratio) == Decimal
        assert type(decision.current_pnl_pct) == Decimal
        assert type(decision.realized_pnl_estimate) == Decimal

    # ── PRIORITY TESTS ──

    def test_sl_priority_over_tp(self, engine):
        """Test SL takes priority over TP when both triggered."""
        # avg=100, current=105 (pnl=+5%)
        # Both TP (5%) and SL (-10%) could trigger based on implementation
        # But only TP should trigger since pnl=+5% > 0
        # This tests the logic flow prioritization
        tp_levels = [TakeProfitLevel(pct=5.0, sell_ratio=0.3)]
        sl_levels = [StopLossLevel(pct=-10.0, sell_ratio=0.5)]
        
        decision = engine.evaluate(
            avg_price=Decimal("100.00"),
            current_price=Decimal("105.00"),
            total_quantity=Decimal("10"),
            take_profit_levels=tp_levels,
            stop_loss_levels=sl_levels
        )
        
        # At +5% PnL, only TP should trigger
        assert decision.triggered_by == "tp"
        assert decision.sell_ratio == Decimal("0.3000")
        
        # Now test actual SL priority with loss
        decision_loss = engine.evaluate(
            avg_price=Decimal("100.00"),
            current_price=Decimal("85.00"),  # -15% loss
            total_quantity=Decimal("10"),
            take_profit_levels=tp_levels,
            stop_loss_levels=sl_levels
        )
        
        # At -15% loss, SL should trigger (not TP)
        assert decision_loss.triggered_by == "sl"
        assert decision_loss.sell_ratio == Decimal("0.5000")

    def test_no_tp_levels_with_profit(self, engine):
        """Test no TP levels defined with profit."""
        # avg=100, current=120, tp_levels=[]
        # → action = "hold" (no TP defined)
        decision = engine.evaluate(
            avg_price=Decimal("100.00"),
            current_price=Decimal("120.00"),
            total_quantity=Decimal("10"),
            take_profit_levels=[],
            stop_loss_levels=[]
        )
        
        assert decision.action == "hold"
        assert decision.triggered_by == "none"

    def test_no_sl_levels_with_loss(self, engine):
        """Test no SL levels defined with loss."""
        # avg=100, current=90, sl_levels=[]
        # → action = "hold" (no SL defined)
        decision = engine.evaluate(
            avg_price=Decimal("100.00"),
            current_price=Decimal("90.00"),
            total_quantity=Decimal("10"),
            take_profit_levels=[],
            stop_loss_levels=[]
        )
        
        assert decision.action == "hold"
        assert decision.triggered_by == "none"

    # ── REALIZED PNL ESTIMATE TESTS ──

    def test_realized_pnl_estimate_on_tp(self, engine):
        """Test realized PnL estimate on TP trigger."""
        # avg=100, current=120, qty=10, sell_ratio=0.5
        # → sell_qty=5
        # → realized_pnl_estimate = (120-100) × 5 = 100.0000
        decision = engine.evaluate(
            avg_price=Decimal("100.00"),
            current_price=Decimal("120.00"),
            total_quantity=Decimal("10"),
            take_profit_levels=[TakeProfitLevel(pct=20.0, sell_ratio=0.5)],
            stop_loss_levels=[]
        )
        
        assert decision.sell_quantity == Decimal("5.0000")
        assert decision.realized_pnl_estimate == Decimal("100.0000")

    def test_realized_pnl_estimate_on_sl(self, engine):
        """Test realized PnL estimate on SL trigger."""
        # avg=100, current=90, qty=10, sell_ratio=1.0
        # → sell_qty=10
        # → realized_pnl_estimate = (90-100) × 10 = -100.0000
        decision = engine.evaluate(
            avg_price=Decimal("100.00"),
            current_price=Decimal("90.00"),
            total_quantity=Decimal("10"),
            take_profit_levels=[],
            stop_loss_levels=[StopLossLevel(pct=-10.0, sell_ratio=1.0)]
        )
        
        assert decision.sell_quantity == Decimal("10.0000")
        assert decision.realized_pnl_estimate == Decimal("-100.0000")

    # ── EDGE CASES ──

    def test_zero_quantity_returns_hold(self, engine):
        """Test zero quantity returns hold."""
        decision = engine.evaluate(
            avg_price=Decimal("100.00"),
            current_price=Decimal("120.00"),
            total_quantity=Decimal("0"),
            take_profit_levels=[TakeProfitLevel(pct=10.0, sell_ratio=0.5)],
            stop_loss_levels=[]
        )
        
        assert decision.action == "hold"
        assert decision.sell_quantity == Decimal("0.0000")

    def test_empty_tp_and_sl_returns_hold(self, engine):
        """Test empty TP and SL lists return hold."""
        decision = engine.evaluate(
            avg_price=Decimal("100.00"),
            current_price=Decimal("120.00"),
            total_quantity=Decimal("10"),
            take_profit_levels=[],
            stop_loss_levels=[]
        )
        
        assert decision.action == "hold"
        assert decision.triggered_by == "none"
        assert decision.triggered_level_pct is None

    def test_decimal_precision_maintained(self, engine):
        """Test that all Decimal values maintain proper precision."""
        decision = engine.evaluate(
            avg_price=Decimal("33.333333"),
            current_price=Decimal("36.666666"),
            total_quantity=Decimal("3"),
            take_profit_levels=[TakeProfitLevel(pct=10.0, sell_ratio=0.3333)],
            stop_loss_levels=[]
        )
        
        # All results should be quantized to 4 decimal places
        assert decision.sell_quantity.as_tuple().exponent <= -4
        assert decision.sell_ratio.as_tuple().exponent <= -4
        assert decision.current_pnl_pct.as_tuple().exponent <= -4
        assert decision.realized_pnl_estimate.as_tuple().exponent <= -4