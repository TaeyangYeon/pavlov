"""
Unit tests for BehaviorAnalyzer.
Tests AI alignment rate calculation, impulse pattern detection.
"""

import pytest
from datetime import datetime, timedelta
from app.domain.behavior.analyzer import BehaviorAnalyzer
from app.domain.behavior.schemas import BehaviorReport, ImpulsePattern


class TestBehaviorAnalyzer:
    """Test behavioral pattern analysis engine."""

    def setup_method(self):
        self.analyzer = BehaviorAnalyzer()
        self.user_id = "test-user-123"
        self.base_time = datetime(2024, 1, 15, 10, 0, 0)

    def create_decision(self, ticker="AAPL", action="buy", ai_suggested=True,
                       hours_ago=0, notes=""):
        """Helper to create decision data."""
        return {
            "ticker": ticker,
            "action": action,
            "price": 150.0,
            "quantity": 10.0,
            "ai_suggested": ai_suggested,
            "notes": notes,
            "created_at": self.base_time - timedelta(hours=hours_ago),
        }

    def test_alignment_rate_all_aligned(self):
        """Test alignment rate when all decisions are AI-aligned."""
        decisions = [
            self.create_decision(ai_suggested=True),
            self.create_decision(ai_suggested=True),
            self.create_decision(ai_suggested=True),
            self.create_decision(ai_suggested=True),
            self.create_decision(ai_suggested=True),
        ]

        report = self.analyzer.analyze(self.user_id, decisions)

        assert report.ai_alignment_rate == 1.0
        assert report.ai_aligned_count == 5
        assert report.ai_contradicted_count == 0
        assert report.total_trades == 5

    def test_alignment_rate_none_aligned(self):
        """Test alignment rate when no decisions are AI-aligned."""
        decisions = [
            self.create_decision(ai_suggested=False),
            self.create_decision(ai_suggested=False),
            self.create_decision(ai_suggested=False),
            self.create_decision(ai_suggested=False),
            self.create_decision(ai_suggested=False),
        ]

        report = self.analyzer.analyze(self.user_id, decisions)

        assert report.ai_alignment_rate == 0.0
        assert report.ai_aligned_count == 0
        assert report.ai_contradicted_count == 5

    def test_alignment_rate_partial(self):
        """Test partial alignment rate calculation."""
        decisions = [
            self.create_decision(ai_suggested=True),   # aligned
            self.create_decision(ai_suggested=True),   # aligned  
            self.create_decision(ai_suggested=True),   # aligned
            self.create_decision(ai_suggested=False),  # contradicted
            self.create_decision(ai_suggested=False, notes="No AI strategy available"),  # no data
        ]

        report = self.analyzer.analyze(self.user_id, decisions)

        # 3 aligned out of 4 with AI data = 0.75
        assert report.ai_alignment_rate == 0.75
        assert report.ai_aligned_count == 3
        assert report.ai_contradicted_count == 1
        assert report.no_ai_data_count == 1

    def test_alignment_rate_zero_trades(self):
        """Test alignment rate with no trades."""
        decisions = []

        report = self.analyzer.analyze(self.user_id, decisions)

        assert report.ai_alignment_rate == 0.0
        assert report.total_trades == 0
        assert report.ai_aligned_count == 0

    def test_alignment_rate_exact_known_value(self):
        """Test exact known alignment rate value."""
        decisions = [
            self.create_decision(ai_suggested=True),   # 1
            self.create_decision(ai_suggested=True),   # 2
            self.create_decision(ai_suggested=False),  # 3 - not aligned
            self.create_decision(ai_suggested=True),   # 4
            self.create_decision(ai_suggested=False),  # 5 - not aligned  
            self.create_decision(ai_suggested=True),   # 6
        ]

        report = self.analyzer.analyze(self.user_id, decisions)

        # 4 aligned out of 6 = 0.6667 (rounded to 4dp)
        assert report.ai_alignment_rate == 0.6667
        assert report.ai_aligned_count == 4
        assert report.ai_contradicted_count == 2

    @pytest.mark.parametrize("hours_between,expected_impulse", [
        (2, True),    # buy then sell 2h later → rapid reversal
        (12, True),   # still within 24h → rapid reversal  
        (23, True),   # 23h → still within 24h window
        (24, False),  # exactly 24h → NOT impulse (strict <)
        (25, False),  # beyond 24h → no impulse
    ])
    def test_rapid_reversal_detection(self, hours_between, expected_impulse):
        """Test rapid reversal pattern detection with various time windows."""
        decisions = [
            self.create_decision(action="buy", hours_ago=hours_between),
            self.create_decision(action="sell", hours_ago=0),
        ]

        report = self.analyzer.analyze(self.user_id, decisions)

        if expected_impulse:
            assert report.impulse_trade_count == 1
            assert len(report.patterns) == 1
            assert report.patterns[0].pattern_type == "rapid_reversal"
            assert report.patterns[0].ticker == "AAPL"
        else:
            assert report.impulse_trade_count == 0
            assert len([p for p in report.patterns if p.pattern_type == "rapid_reversal"]) == 0

    def test_overtrading_detection_3_times_in_7_days(self):
        """Test overtrading detection when 3+ trades in 7 days."""
        decisions = [
            self.create_decision(ticker="AAPL", hours_ago=24),    # 1 day ago
            self.create_decision(ticker="AAPL", hours_ago=48),    # 2 days ago
            self.create_decision(ticker="AAPL", hours_ago=96),    # 4 days ago
            self.create_decision(ticker="MSFT", hours_ago=12),    # Only 1 trade
        ]

        report = self.analyzer.analyze(self.user_id, decisions)

        assert "AAPL" in report.overtrading_tickers
        assert "MSFT" not in report.overtrading_tickers

    def test_overtrading_not_triggered_under_threshold(self):
        """Test overtrading not triggered with only 2 trades."""
        decisions = [
            self.create_decision(ticker="AAPL", hours_ago=24),
            self.create_decision(ticker="AAPL", hours_ago=48),
        ]

        report = self.analyzer.analyze(self.user_id, decisions)

        assert "AAPL" not in report.overtrading_tickers
        assert len(report.overtrading_tickers) == 0

    def test_overtrading_multiple_tickers(self):
        """Test overtrading detection across multiple tickers."""
        decisions = [
            # AAPL: 4 trades in 7 days → overtrading
            self.create_decision(ticker="AAPL", hours_ago=12),
            self.create_decision(ticker="AAPL", hours_ago=24),
            self.create_decision(ticker="AAPL", hours_ago=48),
            self.create_decision(ticker="AAPL", hours_ago=96),
            # MSFT: 2 trades in 7 days → not overtrading
            self.create_decision(ticker="MSFT", hours_ago=24),
            self.create_decision(ticker="MSFT", hours_ago=48),
        ]

        report = self.analyzer.analyze(self.user_id, decisions)

        assert "AAPL" in report.overtrading_tickers
        assert "MSFT" not in report.overtrading_tickers
        assert len(report.overtrading_tickers) == 1

    def test_avg_holding_days_calculation(self):
        """Test average holding days calculation."""
        # Position opened Jan 1, closed Jan 11 → 10 days
        # Position opened Jan 5, closed Jan 10 → 5 days
        # Expected average: 7.5 days
        base = datetime(2024, 1, 1, 10, 0, 0)
        decisions = [
            {
                "ticker": "AAPL",
                "action": "buy", 
                "price": 150.0,
                "quantity": 10.0,
                "ai_suggested": True,
                "notes": "",
                "created_at": base,  # Jan 1
            },
            {
                "ticker": "AAPL",
                "action": "sell",
                "price": 155.0, 
                "quantity": 10.0,
                "ai_suggested": True,
                "notes": "",
                "created_at": base + timedelta(days=10),  # Jan 11
            },
            {
                "ticker": "MSFT",
                "action": "buy",
                "price": 300.0,
                "quantity": 5.0, 
                "ai_suggested": True,
                "notes": "",
                "created_at": base + timedelta(days=4),  # Jan 5
            },
            {
                "ticker": "MSFT",
                "action": "sell",
                "price": 305.0,
                "quantity": 5.0,
                "ai_suggested": True, 
                "notes": "",
                "created_at": base + timedelta(days=9),  # Jan 10
            }
        ]

        report = self.analyzer.analyze(self.user_id, decisions)

        assert report.avg_holding_days == 7.5

    def test_avg_holding_days_no_closed_positions(self):
        """Test average holding days when no positions are closed."""
        decisions = [
            self.create_decision(action="buy"),
            self.create_decision(action="buy", ticker="MSFT"),
        ]

        report = self.analyzer.analyze(self.user_id, decisions)

        assert report.avg_holding_days == 0.0

    def test_most_traded_ticker(self):
        """Test most traded ticker identification."""
        decisions = [
            # AAPL: 5 trades
            self.create_decision(ticker="AAPL"),
            self.create_decision(ticker="AAPL"),
            self.create_decision(ticker="AAPL"),
            self.create_decision(ticker="AAPL"),
            self.create_decision(ticker="AAPL"),
            # MSFT: 3 trades
            self.create_decision(ticker="MSFT"),
            self.create_decision(ticker="MSFT"), 
            self.create_decision(ticker="MSFT"),
            # GOOGL: 1 trade
            self.create_decision(ticker="GOOGL"),
        ]

        report = self.analyzer.analyze(self.user_id, decisions)

        assert report.most_traded_ticker == "AAPL"

    def test_most_traded_ticker_none_on_empty(self):
        """Test most traded ticker returns None when no trades."""
        decisions = []

        report = self.analyzer.analyze(self.user_id, decisions)

        assert report.most_traded_ticker is None