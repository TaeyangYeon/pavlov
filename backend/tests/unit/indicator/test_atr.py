"""
Unit tests for ATRIndicator.
Tests Average True Range calculation with Wilder's smoothing.
"""

import pytest
from app.domain.indicator.atr import ATRIndicator
from app.domain.indicator.exceptions import InsufficientDataError
from app.domain.indicator.interfaces import IndicatorPort


class TestATRIndicator:
    """Test ATR calculation with known values and edge cases."""

    @pytest.fixture
    def indicator(self):
        """ATR indicator instance."""
        return ATRIndicator()

    @pytest.fixture
    def atr_test_data(self):
        """15-candle dataset for ATR verification."""
        # Manual test data with known High, Low, Close values
        candles = [
            {"high": 48.70, "low": 47.79, "close": 48.16},
            {"high": 48.72, "low": 48.14, "close": 48.61},
            {"high": 48.90, "low": 48.39, "close": 48.75},
            {"high": 48.87, "low": 48.37, "close": 48.63},
            {"high": 48.82, "low": 48.24, "close": 48.74},
            {"high": 49.05, "low": 48.64, "close": 49.03},
            {"high": 49.20, "low": 48.94, "close": 49.07},
            {"high": 49.35, "low": 48.86, "close": 49.32},
            {"high": 49.92, "low": 49.50, "close": 49.91},
            {"high": 50.19, "low": 49.87, "close": 50.13},
            {"high": 50.12, "low": 49.20, "close": 49.53},
            {"high": 49.66, "low": 48.90, "close": 49.50},
            {"high": 49.88, "low": 49.43, "close": 49.75},
            {"high": 50.19, "low": 49.73, "close": 50.03},
            {"high": 50.36, "low": 49.26, "close": 50.31},
        ]

        return [
            {
                "ticker": "TEST",
                "market": "US",
                "date": f"2024-01-{i+1:02d}",
                "open": candle["close"],
                "high": candle["high"],
                "low": candle["low"],
                "close": candle["close"],
                "volume": 1000000,
            }
            for i, candle in enumerate(candles)
        ]

    @pytest.fixture
    def high_volatility_data(self):
        """Data with high volatility for ATR > 0."""
        return [
            {
                "ticker": "VOLATILE",
                "market": "US",
                "date": f"2024-01-{i+1:02d}",
                "open": 100.0,
                "high": 105.0,  # 5% range
                "low": 95.0,
                "close": 100.0,
                "volume": 1000000,
            }
            for i in range(15)
        ]

    def test_atr_inherits_indicator_port(self, indicator):
        """ATR indicator must inherit from IndicatorPort."""
        assert isinstance(indicator, IndicatorPort)

    def test_atr_indicator_name_is_atr_14(self, indicator):
        """ATR indicator name must be 'atr_14'."""
        assert indicator.indicator_name == "atr_14"

    def test_atr_returns_positive_value(self, indicator, atr_test_data):
        """ATR must always return positive value."""
        result = indicator.calculate(atr_test_data)
        atr_value = result["atr_14"]
        assert atr_value > 0

    def test_atr_true_range_calculation(self, indicator, atr_test_data):
        """ATR should be reasonable value for test dataset."""
        result = indicator.calculate(atr_test_data)
        atr_value = result["atr_14"]
        # For the given dataset, ATR should be in reasonable range
        assert 0.5 <= atr_value <= 2.0

    def test_atr_raises_on_insufficient_data(self, indicator):
        """ATR must raise InsufficientDataError with < 15 candles."""
        # Only 10 candles (insufficient for 14-period ATR)
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

        assert exc_info.value.indicator_name == "atr_14"
        assert exc_info.value.required == 15
        assert exc_info.value.actual == 10

    def test_atr_high_volatility(self, indicator, high_volatility_data):
        """ATR should be higher for high volatility data."""
        result = indicator.calculate(high_volatility_data)
        atr_value = result["atr_14"]
        # High volatility should produce significant ATR
        assert atr_value > 1.0
