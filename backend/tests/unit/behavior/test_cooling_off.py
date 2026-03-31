"""
Unit tests for CoolingOffGate.
Tests exact boundary conditions and cooling-off logic.
"""

import pytest
from datetime import datetime, timedelta

from app.domain.behavior.cooling_off import CoolingOffGate
from app.domain.behavior.schemas import CoolingOffResult


class TestCoolingOffGate:
    """Test cooling-off period evaluation logic."""

    def setup_method(self):
        self.gate = CoolingOffGate()
        self.base_time = datetime(2024, 1, 15, 10, 0, 0)
        self.ticker = "AAPL"
        self.cooling_off_minutes = 30

    def test_within_cooling_off_period(self):
        """Test trade within cooling-off period."""
        last_alert = self.base_time - timedelta(minutes=10)
        trade_time = self.base_time

        result = self.gate.check(
            ticker=self.ticker,
            trade_time=trade_time,
            last_alert_time=last_alert,
            last_ai_recommendation="hold",
            cooling_off_minutes=self.cooling_off_minutes,
        )

        assert result.is_within_cooling_off is True
        assert result.minutes_elapsed == 10.0
        assert result.minutes_remaining == 20.0
        assert result.cooling_off_minutes == 30
        assert result.ticker == "AAPL"
        assert result.last_ai_recommendation == "hold"

    def test_after_cooling_off_period(self):
        """Test trade after cooling-off period expires."""
        last_alert = self.base_time - timedelta(minutes=45)
        trade_time = self.base_time

        result = self.gate.check(
            ticker=self.ticker,
            trade_time=trade_time,
            last_alert_time=last_alert,
            last_ai_recommendation="buy",
            cooling_off_minutes=self.cooling_off_minutes,
        )

        assert result.is_within_cooling_off is False
        assert result.minutes_elapsed == 45.0
        assert result.minutes_remaining == 0.0

    def test_exactly_at_boundary(self):
        """Test exactly at 30 minutes - should be outside cooling-off."""
        last_alert = self.base_time - timedelta(minutes=30)
        trade_time = self.base_time

        result = self.gate.check(
            ticker=self.ticker,
            trade_time=trade_time,
            last_alert_time=last_alert,
            last_ai_recommendation="hold",
            cooling_off_minutes=self.cooling_off_minutes,
        )

        assert result.is_within_cooling_off is False
        assert result.minutes_elapsed == 30.0
        assert result.minutes_remaining == 0.0

    def test_no_previous_alert(self):
        """Test when no previous alert exists."""
        result = self.gate.check(
            ticker=self.ticker,
            trade_time=self.base_time,
            last_alert_time=None,
            last_ai_recommendation=None,
            cooling_off_minutes=self.cooling_off_minutes,
        )

        assert result.is_within_cooling_off is False
        assert result.minutes_elapsed == 0.0
        assert result.minutes_remaining == 0.0
        assert result.last_alert_time is None
        assert result.last_ai_recommendation is None

    def test_cooling_off_with_custom_minutes(self):
        """Test with custom cooling-off period."""
        custom_cooling_off = 60
        last_alert = self.base_time - timedelta(minutes=30)
        trade_time = self.base_time

        result = self.gate.check(
            ticker=self.ticker,
            trade_time=trade_time,
            last_alert_time=last_alert,
            last_ai_recommendation="sell",
            cooling_off_minutes=custom_cooling_off,
        )

        assert result.is_within_cooling_off is True
        assert result.minutes_elapsed == 30.0
        assert result.minutes_remaining == 30.0
        assert result.cooling_off_minutes == 60

    def test_cooling_off_result_has_ticker(self):
        """Test that result includes ticker information."""
        result = self.gate.check(
            ticker="MSFT",
            trade_time=self.base_time,
            last_alert_time=None,
            last_ai_recommendation=None,
            cooling_off_minutes=30,
        )

        assert result.ticker == "MSFT"

    def test_cooling_off_result_has_recommendation(self):
        """Test that result includes AI recommendation."""
        last_alert = self.base_time - timedelta(minutes=10)
        result = self.gate.check(
            ticker=self.ticker,
            trade_time=self.base_time,
            last_alert_time=last_alert,
            last_ai_recommendation="full_exit",
            cooling_off_minutes=30,
        )

        assert result.last_ai_recommendation == "full_exit"