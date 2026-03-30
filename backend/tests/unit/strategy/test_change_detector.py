"""
Unit tests for ChangeDetector (TDD - Red Phase).
All tests should FAIL before implementation.
"""

from decimal import Decimal

import pytest

from app.domain.strategy.change_detector import ChangeDetector
from app.domain.strategy.schemas import UnifiedStrategy


class TestChangeDetector:
    """Test suite for ChangeDetector."""

    def setup_method(self):
        """Setup test instance."""
        self.detector = ChangeDetector()

    def test_no_change_when_action_and_qty_same(self):
        """No change when action and quantity are the same"""
        current = UnifiedStrategy(
            ticker="AAPL",
            market="US",
            final_action="hold",
            action_source="ai",
            confidence=Decimal("0.8"),
            rationale="No signal",
            sell_quantity=Decimal("0.0000"),
            realized_pnl_estimate=Decimal("0.0000")
        )
        
        last = {
            "ticker": "AAPL",
            "action": "hold",
            "sell_quantity": "0.0000"
        }
        
        result = self.detector.has_changed(current, last)
        assert result == False

    def test_change_detected_on_action_change(self):
        """Change detected when action changes"""
        current = UnifiedStrategy(
            ticker="AAPL",
            market="US",
            final_action="partial_sell",
            action_source="position_engine",
            confidence=Decimal("1.0"),
            rationale="TP triggered",
            sell_quantity=Decimal("5.0"),
            realized_pnl_estimate=Decimal("100.0")
        )
        
        last = {
            "ticker": "AAPL",
            "action": "hold",
            "sell_quantity": "0.0000"
        }
        
        result = self.detector.has_changed(current, last)
        assert result == True

    def test_change_detected_on_quantity_change(self):
        """Change detected when sell quantity changes"""
        current = UnifiedStrategy(
            ticker="AAPL",
            market="US",
            final_action="partial_sell",
            action_source="position_engine",
            confidence=Decimal("1.0"),
            rationale="TP triggered",
            sell_quantity=Decimal("3.0"),
            realized_pnl_estimate=Decimal("60.0")
        )
        
        last = {
            "ticker": "AAPL",
            "action": "partial_sell",
            "sell_quantity": "5.0000"
        }
        
        result = self.detector.has_changed(current, last)
        assert result == True

    def test_no_change_on_quantity_rounding(self):
        """No change when quantities round to same 2 decimal places"""
        current = UnifiedStrategy(
            ticker="AAPL",
            market="US",
            final_action="partial_sell",
            action_source="position_engine",
            confidence=Decimal("1.0"),
            rationale="TP triggered",
            sell_quantity=Decimal("5.0001"),
            realized_pnl_estimate=Decimal("100.0")
        )
        
        last = {
            "ticker": "AAPL",
            "action": "partial_sell",
            "sell_quantity": "5.0000"
        }
        
        result = self.detector.has_changed(current, last)
        assert result == False  # Both round to 5.00

    def test_change_when_no_previous_strategy(self):
        """Always changed when no previous strategy exists"""
        current = UnifiedStrategy(
            ticker="AAPL",
            market="US",
            final_action="hold",
            action_source="ai",
            confidence=Decimal("0.6"),
            rationale="First run",
            sell_quantity=Decimal("0.0000"),
            realized_pnl_estimate=Decimal("0.0000")
        )
        
        result = self.detector.has_changed(current, None)
        assert result == True

    def test_change_on_ticker_mismatch(self):
        """Change when tickers don't match"""
        current = UnifiedStrategy(
            ticker="MSFT",
            market="US",
            final_action="hold",
            action_source="ai",
            confidence=Decimal("0.7"),
            rationale="Different ticker",
            sell_quantity=Decimal("0.0000"),
            realized_pnl_estimate=Decimal("0.0000")
        )
        
        last = {
            "ticker": "AAPL",  # Different ticker
            "action": "hold",
            "sell_quantity": "0.0000"
        }
        
        result = self.detector.has_changed(current, last)
        assert result == True

    def test_quantity_precision_boundary(self):
        """Test 2-decimal precision boundary conditions"""
        current = UnifiedStrategy(
            ticker="AAPL",
            market="US",
            final_action="partial_sell",
            action_source="position_engine",
            confidence=Decimal("1.0"),
            rationale="TP triggered",
            sell_quantity=Decimal("5.005"),  # Rounds to 5.01
            realized_pnl_estimate=Decimal("100.0")
        )
        
        last = {
            "ticker": "AAPL",
            "action": "partial_sell",
            "sell_quantity": "5.000"  # Rounds to 5.00
        }
        
        result = self.detector.has_changed(current, last)
        assert result == True  # 5.01 != 5.00

    def test_no_change_with_extra_precision(self):
        """No change when difference is within 2dp precision"""
        current = UnifiedStrategy(
            ticker="AAPL",
            market="US",
            final_action="partial_sell",
            action_source="position_engine",
            confidence=Decimal("1.0"),
            rationale="TP triggered",
            sell_quantity=Decimal("5.0049"),  # Rounds to 5.00
            realized_pnl_estimate=Decimal("100.0")
        )
        
        last = {
            "ticker": "AAPL",
            "action": "partial_sell",
            "sell_quantity": "5.0000"  # Rounds to 5.00
        }
        
        result = self.detector.has_changed(current, last)
        assert result == False  # Both round to 5.00

    def test_missing_last_strategy_fields(self):
        """Handle missing fields in last strategy gracefully"""
        current = UnifiedStrategy(
            ticker="AAPL",
            market="US",
            final_action="buy",
            action_source="ai",
            confidence=Decimal("0.8"),
            rationale="Buy signal",
            sell_quantity=Decimal("0.0000"),
            realized_pnl_estimate=Decimal("0.0000")
        )
        
        # Missing sell_quantity field
        last = {
            "ticker": "AAPL",
            "action": "buy"
            # sell_quantity missing
        }
        
        result = self.detector.has_changed(current, last)
        # Should handle gracefully - missing qty defaults to 0
        assert result == False  # Both are 0.00