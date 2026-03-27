"""
Unit tests for VolumeRatioIndicator.
Tests volume ratio calculation (today / 20-day average).
"""

import pytest
from app.domain.indicator.exceptions import InsufficientDataError
from app.domain.indicator.interfaces import IndicatorPort
from app.domain.indicator.volume_ratio import VolumeRatioIndicator


class TestVolumeRatioIndicator:
    """Test volume ratio calculation with known values."""

    @pytest.fixture
    def indicator(self):
        """Volume ratio indicator instance."""
        return VolumeRatioIndicator()

    @pytest.fixture
    def high_volume_data(self):
        """Data with high volume today vs average."""
        # 20 days of 1M volume, then today with 2M volume
        volumes = [1000000] * 20 + [2000000]  # Last day = 2x average
        return [
            {
                "ticker": "HIGH_VOL",
                "market": "US",
                "date": f"2024-01-{i+1:02d}",
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.0,
                "volume": volume,
            }
            for i, volume in enumerate(volumes)
        ]

    @pytest.fixture
    def low_volume_data(self):
        """Data with low volume today vs average."""
        # 20 days of 1M volume, then today with 500K volume
        volumes = [1000000] * 20 + [500000]  # Last day = 0.5x average
        return [
            {
                "ticker": "LOW_VOL",
                "market": "US",
                "date": f"2024-01-{i+1:02d}",
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.0,
                "volume": volume,
            }
            for i, volume in enumerate(volumes)
        ]

    @pytest.fixture
    def average_volume_data(self):
        """Data with average volume today."""
        # 20 days of 1M volume, then today also with 1M volume
        volumes = [1000000] * 21  # All days same volume
        return [
            {
                "ticker": "AVG_VOL",
                "market": "US",
                "date": f"2024-01-{i+1:02d}",
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.0,
                "volume": volume,
            }
            for i, volume in enumerate(volumes)
        ]

    def test_volume_ratio_inherits_indicator_port(self, indicator):
        """Volume ratio indicator must inherit from IndicatorPort."""
        assert isinstance(indicator, IndicatorPort)

    def test_volume_ratio_indicator_name(self, indicator):
        """Volume ratio indicator name must be 'volume_ratio'."""
        assert indicator.indicator_name == "volume_ratio"

    def test_volume_ratio_above_one_on_high_volume(self, indicator, high_volume_data):
        """Volume ratio should be 2.0 for 2x average volume."""
        result = indicator.calculate(high_volume_data)
        volume_ratio = result["volume_ratio"]
        # Today vol = 2M, avg 20-day vol = 1M, ratio = 2.0
        assert abs(volume_ratio - 2.0) < 0.001

    def test_volume_ratio_below_one_on_low_volume(self, indicator, low_volume_data):
        """Volume ratio should be 0.5 for 0.5x average volume."""
        result = indicator.calculate(low_volume_data)
        volume_ratio = result["volume_ratio"]
        # Today vol = 500K, avg 20-day vol = 1M, ratio = 0.5
        assert abs(volume_ratio - 0.5) < 0.001

    def test_volume_ratio_equals_one_on_average_volume(
        self, indicator, average_volume_data
    ):
        """Volume ratio should be 1.0 for average volume."""
        result = indicator.calculate(average_volume_data)
        volume_ratio = result["volume_ratio"]
        # Today vol = 1M, avg 20-day vol = 1M, ratio = 1.0
        assert abs(volume_ratio - 1.0) < 0.001

    def test_volume_ratio_raises_on_insufficient_data(self, indicator):
        """Volume ratio must raise InsufficientDataError with < 21 candles."""
        # Only 15 candles (insufficient for 20-day average + today)
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

        assert exc_info.value.indicator_name == "volume_ratio"
        assert exc_info.value.required == 21
        assert exc_info.value.actual == 15
