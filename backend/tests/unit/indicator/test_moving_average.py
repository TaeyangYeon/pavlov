"""
Unit tests for MovingAverageIndicator.
Tests simple arithmetic mean calculations for MA20 and MA60.
"""

import pytest
from app.domain.indicator.exceptions import InsufficientDataError
from app.domain.indicator.interfaces import IndicatorPort
from app.domain.indicator.moving_average import MovingAverageIndicator


class TestMovingAverageIndicator:
    """Test moving average calculations with known values."""

    @pytest.fixture
    def indicator(self):
        """Moving average indicator instance."""
        return MovingAverageIndicator()

    @pytest.fixture
    def ma20_data(self):
        """60 candles with last 20 closes 1.0 to 20.0 for MA20 = 10.5."""
        # First 40 candles with constant close price of 100.0
        # Last 20 candles with closes 1.0 to 20.0
        closes = [100.0] * 40 + [float(i) for i in range(1, 21)]
        return [
            {
                "ticker": "TEST",
                "market": "US",
                "date": f"2024-01-{i:02d}",
                "open": close,
                "high": close + 0.5,
                "low": close - 0.5,
                "close": close,
                "volume": 1000000,
            }
            for i, close in enumerate(closes, 1)
        ]

    @pytest.fixture
    def ma60_data(self):
        """60 candles with closes 1.0 to 60.0 for MA60 = 30.5."""
        closes = [float(i) for i in range(1, 61)]  # 1.0 to 60.0
        return [
            {
                "ticker": "TEST",
                "market": "US",
                "date": f"2024-01-{i:02d}",
                "open": close,
                "high": close + 0.5,
                "low": close - 0.5,
                "close": close,
                "volume": 1000000,
            }
            for i, close in enumerate(closes, 1)
        ]

    def test_moving_average_inherits_indicator_port(self, indicator):
        """Moving average indicator must inherit from IndicatorPort."""
        assert isinstance(indicator, IndicatorPort)

    def test_moving_average_indicator_name(self, indicator):
        """Moving average indicator name must be 'moving_average'."""
        assert indicator.indicator_name == "moving_average"

    def test_ma20_known_value(self, indicator, ma20_data):
        """MA20 of [1,2,...,20] should be 10.5."""
        result = indicator.calculate(ma20_data)
        ma20_value = result["ma_20"]
        # Sum of 1 to 20 = 210, average = 210/20 = 10.5
        assert ma20_value == 10.5

    def test_ma60_known_value(self, indicator, ma60_data):
        """MA60 of [1,2,...,60] should be 30.5."""
        result = indicator.calculate(ma60_data)
        ma60_value = result["ma_60"]
        # Sum of 1 to 60 = 1830, average = 1830/60 = 30.5
        assert ma60_value == 30.5

    def test_ma20_raises_on_insufficient_data(self, indicator):
        """Moving average must raise InsufficientDataError with < 60 candles."""
        # Only 15 candles (insufficient for MA60, which determines minimum)
        insufficient_data = [
            {
                "ticker": "TEST",
                "market": "US",
                "date": f"2024-01-{i+1:02d}",
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.0,
                "volume": 1000000,
            }
            for i in range(15)
        ]

        with pytest.raises(InsufficientDataError) as exc_info:
            indicator.calculate(insufficient_data)

        assert exc_info.value.indicator_name == "moving_average"
        assert exc_info.value.required == 60
        assert exc_info.value.actual == 15

    def test_ma60_raises_on_insufficient_data(self, indicator):
        """Moving average must raise InsufficientDataError with 50 candles."""
        # 50 candles (insufficient for MA60)
        insufficient_data = [
            {
                "ticker": "TEST",
                "market": "US",
                "date": f"2024-01-{i+1:02d}",
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.0,
                "volume": 1000000,
            }
            for i in range(50)
        ]

        with pytest.raises(InsufficientDataError) as exc_info:
            indicator.calculate(insufficient_data)

        assert exc_info.value.indicator_name == "moving_average"
        assert exc_info.value.required == 60
        assert exc_info.value.actual == 50

    def test_both_ma20_and_ma60_returned(self, indicator, ma60_data):
        """Both MA20 and MA60 should be returned in result."""
        result = indicator.calculate(ma60_data)
        assert "ma_20" in result
        assert "ma_60" in result
        assert len(result) == 2
