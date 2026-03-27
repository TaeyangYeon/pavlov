"""
Unit tests for MAAlignmentFilter.
Tests bullish/bearish MA alignment with boundary values.
"""

import pytest
from app.domain.filter.interfaces import FilterPort
from app.domain.filter.ma_alignment_filter import MAAlignmentFilter


class TestMAAlignmentFilter:
    """Test MA alignment filtering for trend detection."""

    @pytest.fixture
    def filter_instance(self):
        """MAAlignmentFilter instance."""
        return MAAlignmentFilter()

    @pytest.fixture
    def sample_stock(self):
        """Sample stock dict matching IndicatorEngine output format."""
        return {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "market": "NASDAQ",
            "close": 110.0,  # bullish: close > ma_20 > ma_60
            "volume_ratio": 2.0,
            "rsi_14": 65.0,
            "ma_20": 105.0,
            "ma_60": 100.0,
            "atr_14": 2.5,
        }

    @pytest.mark.parametrize(
        "close,ma_20,ma_60,expected_pass",
        [
            (110, 105, 100, True),  # bullish: close > ma20 > ma60
            (90, 95, 100, True),  # bearish: close < ma20 < ma60
            (105, 110, 100, False),  # mixed: close < ma20 but ma20 > ma60
            (100, 100, 100, False),  # flat: all equal → FAIL
            (110, 100, 105, False),  # close > ma20 but ma20 < ma60
            (95, 105, 100, False),  # close < ma20 but ma20 > ma60
            (105, 90, 100, False),  # close > ma20 but ma20 < ma60
        ],
    )
    def test_ma_alignment_threshold_boundary(self, close, ma_20, ma_60, expected_pass):
        """MA alignment boundary value testing with parametrized inputs."""
        filter_instance = MAAlignmentFilter()
        stock = {
            "ticker": "TEST",
            "name": "Test Corp",
            "market": "NYSE",
            "close": close,
            "volume_ratio": 1.5,
            "rsi_14": 50.0,
            "ma_20": ma_20,
            "ma_60": ma_60,
            "atr_14": 1.0,
        }

        result = filter_instance.apply([stock])

        if expected_pass:
            assert len(result) == 1
            assert result[0]["ticker"] == "TEST"
        else:
            assert len(result) == 0

    def test_ma_alignment_passes_bullish_trend(self, filter_instance):
        """MAAlignmentFilter passes stocks in clear bullish trend."""
        bullish_stocks = [
            {
                "ticker": "BULL1",
                "close": 120,
                "ma_20": 115,
                "ma_60": 110,
            },  # strong bullish
            {
                "ticker": "BULL2",
                "close": 105,
                "ma_20": 102,
                "ma_60": 100,
            },  # mild bullish
            {
                "ticker": "BULL3",
                "close": 150,
                "ma_20": 140,
                "ma_60": 130,
            },  # very bullish
        ]

        result = filter_instance.apply(bullish_stocks)

        assert len(result) == 3
        for stock in result:
            assert stock["close"] > stock["ma_20"] > stock["ma_60"]

    def test_ma_alignment_passes_bearish_trend(self, filter_instance):
        """MAAlignmentFilter passes stocks in clear bearish trend."""
        bearish_stocks = [
            {
                "ticker": "BEAR1",
                "close": 80,
                "ma_20": 85,
                "ma_60": 90,
            },  # strong bearish
            {"ticker": "BEAR2", "close": 95, "ma_20": 98, "ma_60": 100},  # mild bearish
            {"ticker": "BEAR3", "close": 70, "ma_20": 80, "ma_60": 90},  # very bearish
        ]

        result = filter_instance.apply(bearish_stocks)

        assert len(result) == 3
        for stock in result:
            assert stock["close"] < stock["ma_20"] < stock["ma_60"]

    def test_ma_alignment_rejects_sideways(self, filter_instance):
        """MAAlignmentFilter rejects stocks in sideways/mixed trends."""
        sideways_stocks = [
            {"ticker": "SIDE1", "close": 100, "ma_20": 100, "ma_60": 100},  # flat
            {
                "ticker": "SIDE2",
                "close": 105,
                "ma_20": 110,
                "ma_60": 100,
            },  # close < ma20 but ma20 > ma60
            {
                "ticker": "SIDE3",
                "close": 110,
                "ma_20": 100,
                "ma_60": 105,
            },  # close > ma20 but ma20 < ma60
            {
                "ticker": "SIDE4",
                "close": 95,
                "ma_20": 105,
                "ma_60": 100,
            },  # close < ma20 but ma20 > ma60
        ]

        result = filter_instance.apply(sideways_stocks)

        # All should be filtered out
        assert len(result) == 0

    def test_ma_alignment_empty_input_returns_empty(self, filter_instance):
        """MAAlignmentFilter returns empty list for empty input."""
        result = filter_instance.apply([])

        assert result == []
        assert isinstance(result, list)

    def test_ma_alignment_missing_key_fails_safely(self, filter_instance):
        """Stock without required keys is excluded, no KeyError raised."""
        stocks_missing_keys = [
            {"ticker": "VALID", "close": 110, "ma_20": 105, "ma_60": 100},  # PASS
            {"ticker": "NO_CLOSE", "ma_20": 105, "ma_60": 100},  # missing close → FAIL
            {"ticker": "NO_MA20", "close": 110, "ma_60": 100},  # missing ma_20 → FAIL
            {"ticker": "NO_MA60", "close": 110, "ma_20": 105},  # missing ma_60 → FAIL
        ]

        result = filter_instance.apply(stocks_missing_keys)

        # Only the valid stock should pass
        assert len(result) == 1
        assert result[0]["ticker"] == "VALID"

    def test_ma_alignment_name_is_correct(self, filter_instance):
        """MAAlignmentFilter filter_name property returns correct name."""
        assert filter_instance.filter_name == "ma_alignment_filter"

    def test_ma_alignment_inherits_from_filter_port(self, filter_instance):
        """MAAlignmentFilter must inherit from FilterPort ABC."""
        assert isinstance(filter_instance, FilterPort)

    def test_ma_alignment_does_not_mutate_input(self, filter_instance, sample_stock):
        """MAAlignmentFilter does not mutate the original input list."""
        original_stocks = [sample_stock.copy(), sample_stock.copy()]
        original_length = len(original_stocks)
        original_first_close = original_stocks[0]["close"]

        result = filter_instance.apply(original_stocks)

        # Verify original list is unchanged
        assert len(original_stocks) == original_length
        assert original_stocks[0]["close"] == original_first_close
        assert id(result) != id(original_stocks)  # Different objects
