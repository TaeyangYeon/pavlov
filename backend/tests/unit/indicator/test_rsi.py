"""
Unit tests for RSIIndicator.
Tests Wilder's smoothing RSI calculation with known values.
"""

import pytest
from app.domain.indicator.exceptions import InsufficientDataError
from app.domain.indicator.interfaces import IndicatorPort
from app.domain.indicator.rsi import RSIIndicator


class TestRSIIndicator:
    """Test RSI calculation with known values and edge cases."""

    @pytest.fixture
    def indicator(self):
        """RSI indicator instance."""
        return RSIIndicator()

    @pytest.fixture
    def known_rsi_data(self):
        """16-candle dataset for RSI verification."""
        closes = [
            44.34,
            44.09,
            44.15,
            43.61,
            44.33,
            44.83,
            45.10,
            45.15,
            43.61,
            44.33,
            44.83,
            45.85,
            46.08,
            45.89,
            46.03,
            46.83,
        ]
        return [
            {
                "ticker": "TEST",
                "market": "US",
                "date": f"2024-01-{i+1:02d}",
                "open": close,
                "high": close + 0.5,
                "low": close - 0.5,
                "close": close,
                "volume": 1000000,
            }
            for i, close in enumerate(closes)
        ]

    @pytest.fixture
    def rising_data(self):
        """Data with consistently rising prices for overbought test."""
        closes = [10.0 + i * 0.5 for i in range(20)]  # 10.0 to 19.5
        return [
            {
                "ticker": "RISING",
                "market": "US",
                "date": f"2024-01-{i+1:02d}",
                "open": close,
                "high": close + 0.1,
                "low": close - 0.1,
                "close": close,
                "volume": 1000000,
            }
            for i, close in enumerate(closes)
        ]

    @pytest.fixture
    def falling_data(self):
        """Data with consistently falling prices for oversold test."""
        closes = [20.0 - i * 0.5 for i in range(20)]  # 20.0 to 10.5
        return [
            {
                "ticker": "FALLING",
                "market": "US",
                "date": f"2024-01-{i+1:02d}",
                "open": close,
                "high": close + 0.1,
                "low": close - 0.1,
                "close": close,
                "volume": 1000000,
            }
            for i, close in enumerate(closes)
        ]

    def test_rsi_inherits_indicator_port(self, indicator):
        """RSI indicator must inherit from IndicatorPort."""
        assert isinstance(indicator, IndicatorPort)

    def test_rsi_indicator_name_is_rsi_14(self, indicator):
        """RSI indicator name must be 'rsi_14'."""
        assert indicator.indicator_name == "rsi_14"

    def test_rsi_returns_value_in_range_0_to_100(self, indicator, known_rsi_data):
        """RSI must always return value between 0 and 100."""
        result = indicator.calculate(known_rsi_data)
        rsi_value = result["rsi_14"]
        assert 0 <= rsi_value <= 100

    def test_rsi_known_value(self, indicator, known_rsi_data):
        """RSI of known dataset should be approximately 57.4 (Wilder's smoothing)."""
        result = indicator.calculate(known_rsi_data)
        rsi_value = result["rsi_14"]
        # Expected RSI for this dataset with Wilder's smoothing
        # is around 57.4 (±2.0 tolerance)
        assert abs(rsi_value - 57.4) < 2.0

    def test_rsi_raises_on_insufficient_data(self, indicator):
        """RSI must raise InsufficientDataError with < 15 candles."""
        # Only 10 candles (insufficient for 14-period RSI)
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
            for i in range(10)
        ]

        with pytest.raises(InsufficientDataError) as exc_info:
            indicator.calculate(insufficient_data)

        assert exc_info.value.indicator_name == "rsi_14"
        assert exc_info.value.required == 15
        assert exc_info.value.actual == 10

    def test_rsi_overbought_zone(self, indicator, rising_data):
        """RSI should be > 70 for consistently rising prices."""
        result = indicator.calculate(rising_data)
        rsi_value = result["rsi_14"]
        assert rsi_value > 70

    def test_rsi_oversold_zone(self, indicator, falling_data):
        """RSI should be < 30 for consistently falling prices."""
        result = indicator.calculate(falling_data)
        rsi_value = result["rsi_14"]
        assert rsi_value < 30
