"""
Unit tests for VolumeFilter.
Tests parametrized boundary values and pure function behavior.
"""

import pytest
from app.domain.filter.interfaces import FilterPort
from app.domain.filter.volume_filter import VolumeFilter


class TestVolumeFilter:
    """Test volume ratio filtering with boundary values."""

    @pytest.fixture
    def filter_instance(self):
        """VolumeFilter with default threshold 1.3."""
        return VolumeFilter()

    @pytest.fixture
    def sample_stock(self):
        """Sample stock dict matching IndicatorEngine output format."""
        return {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "market": "NASDAQ",
            "close": 150.0,
            "volume_ratio": 2.0,
            "rsi_14": 65.0,
            "ma_20": 145.0,
            "ma_60": 140.0,
            "atr_14": 2.5,
        }

    @pytest.mark.parametrize(
        "volume_ratio,expected_pass",
        [
            (2.0, True),  # well above threshold
            (1.3, True),  # exact threshold → PASS
            (1.29, False),  # just below → FAIL
            (0.5, False),  # low volume
            (0.0, False),  # zero volume
        ],
    )
    def test_volume_filter_threshold_boundary(self, volume_ratio, expected_pass):
        """Volume filter boundary value testing with parametrized inputs."""
        filter_instance = VolumeFilter(min_volume_ratio=1.3)
        stock = {
            "ticker": "TEST",
            "name": "Test Corp",
            "market": "NYSE",
            "close": 100.0,
            "volume_ratio": volume_ratio,
            "rsi_14": 50.0,
            "ma_20": 100.0,
            "ma_60": 95.0,
            "atr_14": 1.0,
        }

        result = filter_instance.apply([stock])

        if expected_pass:
            assert len(result) == 1
            assert result[0]["ticker"] == "TEST"
        else:
            assert len(result) == 0

    def test_volume_filter_passes_high_volume_stocks(self, filter_instance):
        """VolumeFilter passes stocks with high volume ratio."""
        high_volume_stocks = [
            {"ticker": "AAPL", "volume_ratio": 2.5, "close": 150.0},
            {"ticker": "GOOGL", "volume_ratio": 1.8, "close": 2800.0},
            {"ticker": "MSFT", "volume_ratio": 3.2, "close": 300.0},
        ]

        result = filter_instance.apply(high_volume_stocks)

        assert len(result) == 3
        assert all(stock["volume_ratio"] >= 1.3 for stock in result)

    def test_volume_filter_removes_low_volume_stocks(self, filter_instance):
        """VolumeFilter removes stocks with low volume ratio."""
        mixed_stocks = [
            {"ticker": "HIGH", "volume_ratio": 2.0, "close": 100.0},  # PASS
            {"ticker": "LOW1", "volume_ratio": 0.8, "close": 50.0},  # FAIL
            {"ticker": "LOW2", "volume_ratio": 1.2, "close": 75.0},  # FAIL
            {"ticker": "HIGH2", "volume_ratio": 1.5, "close": 200.0},  # PASS
        ]

        result = filter_instance.apply(mixed_stocks)

        assert len(result) == 2
        assert result[0]["ticker"] == "HIGH"
        assert result[1]["ticker"] == "HIGH2"

    def test_volume_filter_empty_input_returns_empty(self, filter_instance):
        """VolumeFilter returns empty list for empty input."""
        result = filter_instance.apply([])

        assert result == []
        assert isinstance(result, list)

    def test_volume_filter_missing_key_fails_safely(self, filter_instance):
        """Stock without volume_ratio key is excluded, no KeyError raised."""
        stocks_missing_key = [
            {"ticker": "VALID", "volume_ratio": 2.0, "close": 100.0},  # PASS
            {"ticker": "MISSING", "close": 50.0},  # missing volume_ratio → FAIL
            {"ticker": "NONE", "volume_ratio": None, "close": 75.0},  # None → FAIL
        ]

        result = filter_instance.apply(stocks_missing_key)

        # Only the valid stock should pass
        assert len(result) == 1
        assert result[0]["ticker"] == "VALID"

    def test_volume_filter_custom_threshold(self):
        """VolumeFilter with custom threshold works correctly."""
        custom_filter = VolumeFilter(min_volume_ratio=2.0)
        stocks = [
            {"ticker": "HIGH", "volume_ratio": 2.5, "close": 100.0},  # PASS
            {"ticker": "BORDER", "volume_ratio": 2.0, "close": 50.0},  # PASS (exact)
            {
                "ticker": "LOW",
                "volume_ratio": 1.5,
                "close": 75.0,
            },  # FAIL (was good for 1.3)
        ]

        result = custom_filter.apply(stocks)

        assert len(result) == 2
        assert result[0]["ticker"] == "HIGH"
        assert result[1]["ticker"] == "BORDER"

    def test_volume_filter_name_is_correct(self, filter_instance):
        """VolumeFilter filter_name property returns correct name."""
        assert filter_instance.filter_name == "volume_filter"

    def test_volume_filter_inherits_from_filter_port(self, filter_instance):
        """VolumeFilter must inherit from FilterPort ABC."""
        assert isinstance(filter_instance, FilterPort)

    def test_volume_filter_does_not_mutate_input(self, filter_instance, sample_stock):
        """VolumeFilter does not mutate the original input list."""
        original_stocks = [sample_stock.copy(), sample_stock.copy()]
        original_length = len(original_stocks)
        original_first_ticker = original_stocks[0]["ticker"]

        result = filter_instance.apply(original_stocks)

        # Verify original list is unchanged
        assert len(original_stocks) == original_length
        assert original_stocks[0]["ticker"] == original_first_ticker
        assert id(result) != id(original_stocks)  # Different objects
