"""
Unit tests for VolatilityFilter.
Tests ATR/close ratio boundary values and configuration validation.
"""

import pytest
from app.domain.filter.exceptions import FilterConfigError
from app.domain.filter.interfaces import FilterPort
from app.domain.filter.volatility_filter import VolatilityFilter


class TestVolatilityFilter:
    """Test volatility filtering with ATR ratio boundary values."""

    @pytest.fixture
    def filter_instance(self):
        """VolatilityFilter with default range 0.005~0.05."""
        return VolatilityFilter()

    @pytest.fixture
    def sample_stock(self):
        """Sample stock dict matching IndicatorEngine output format."""
        return {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "market": "NASDAQ",
            "close": 100.0,
            "volume_ratio": 2.0,
            "rsi_14": 65.0,
            "ma_20": 105.0,
            "ma_60": 95.0,
            "atr_14": 1.0,  # ratio = 1.0/100.0 = 0.01
        }

    @pytest.mark.parametrize(
        "atr_14,close,expected_pass",
        [
            (1.0, 100.0, True),  # ratio=0.01 → within 0.005~0.05
            (0.4, 100.0, False),  # ratio=0.004 → too low
            (0.5, 100.0, True),  # ratio=0.005 → exact min → PASS
            (5.0, 100.0, True),  # ratio=0.05 → exact max → PASS
            (5.1, 100.0, False),  # ratio=0.051 → too high
            (10.0, 100.0, False),  # ratio=0.1 → too volatile
        ],
    )
    def test_volatility_filter_threshold_boundary(self, atr_14, close, expected_pass):
        """Volatility filter boundary value testing with parametrized inputs."""
        filter_instance = VolatilityFilter(min_atr_ratio=0.005, max_atr_ratio=0.05)
        stock = {
            "ticker": "TEST",
            "name": "Test Corp",
            "market": "NYSE",
            "close": close,
            "volume_ratio": 1.5,
            "rsi_14": 50.0,
            "ma_20": close,
            "ma_60": close,
            "atr_14": atr_14,
        }

        result = filter_instance.apply([stock])

        if expected_pass:
            assert len(result) == 1
            assert result[0]["ticker"] == "TEST"
        else:
            assert len(result) == 0

    def test_volatility_filter_removes_dead_stocks(self, filter_instance):
        """VolatilityFilter removes stocks with too low volatility (dead stocks)."""
        dead_stocks = [
            {"ticker": "DEAD1", "close": 100.0, "atr_14": 0.3},  # ratio=0.003 → too low
            {"ticker": "DEAD2", "close": 200.0, "atr_14": 0.8},  # ratio=0.004 → too low
            {"ticker": "ALIVE", "close": 100.0, "atr_14": 1.0},  # ratio=0.01 → OK
        ]

        result = filter_instance.apply(dead_stocks)

        assert len(result) == 1
        assert result[0]["ticker"] == "ALIVE"

    def test_volatility_filter_removes_too_volatile_stocks(self, filter_instance):
        """VolatilityFilter removes stocks with too high volatility (too risky)."""
        volatile_stocks = [
            {
                "ticker": "RISKY1",
                "close": 100.0,
                "atr_14": 8.0,
            },  # ratio=0.08 → too high
            {"ticker": "RISKY2", "close": 50.0, "atr_14": 10.0},  # ratio=0.2 → too high
            {"ticker": "GOOD", "close": 100.0, "atr_14": 2.0},  # ratio=0.02 → OK
        ]

        result = filter_instance.apply(volatile_stocks)

        assert len(result) == 1
        assert result[0]["ticker"] == "GOOD"

    def test_volatility_filter_empty_input_returns_empty(self, filter_instance):
        """VolatilityFilter returns empty list for empty input."""
        result = filter_instance.apply([])

        assert result == []
        assert isinstance(result, list)

    def test_volatility_filter_missing_key_fails_safely(self, filter_instance):
        """Stock without required keys is excluded, no KeyError raised."""
        stocks_missing_keys = [
            {"ticker": "VALID", "close": 100.0, "atr_14": 1.0},  # PASS
            {"ticker": "NO_ATR", "close": 50.0},  # missing atr_14 → FAIL
            {"ticker": "NO_CLOSE", "atr_14": 2.0},  # missing close → FAIL
            {
                "ticker": "ZERO_CLOSE",
                "close": 0.0,
                "atr_14": 1.0,
            },  # close=0 → ZeroDivision → FAIL
        ]

        result = filter_instance.apply(stocks_missing_keys)

        # Only the valid stock should pass
        assert len(result) == 1
        assert result[0]["ticker"] == "VALID"

    def test_volatility_filter_custom_range(self):
        """VolatilityFilter with custom range works correctly."""
        custom_filter = VolatilityFilter(min_atr_ratio=0.01, max_atr_ratio=0.03)
        stocks = [
            {"ticker": "TOO_LOW", "close": 100.0, "atr_14": 0.8},  # ratio=0.008 → FAIL
            {"ticker": "MIN_OK", "close": 100.0, "atr_14": 1.0},  # ratio=0.01 → PASS
            {"ticker": "MAX_OK", "close": 100.0, "atr_14": 3.0},  # ratio=0.03 → PASS
            {"ticker": "TOO_HIGH", "close": 100.0, "atr_14": 4.0},  # ratio=0.04 → FAIL
        ]

        result = custom_filter.apply(stocks)

        assert len(result) == 2
        assert result[0]["ticker"] == "MIN_OK"
        assert result[1]["ticker"] == "MAX_OK"

    def test_volatility_filter_name_is_correct(self, filter_instance):
        """VolatilityFilter filter_name property returns correct name."""
        assert filter_instance.filter_name == "volatility_filter"

    def test_volatility_filter_inherits_from_filter_port(self, filter_instance):
        """VolatilityFilter must inherit from FilterPort ABC."""
        assert isinstance(filter_instance, FilterPort)

    def test_volatility_filter_invalid_config_raises(self):
        """VolatilityFilter with min > max raises FilterConfigError."""
        with pytest.raises(FilterConfigError) as exc_info:
            VolatilityFilter(min_atr_ratio=0.05, max_atr_ratio=0.01)

        assert exc_info.value.filter_name == "volatility_filter"
        assert "min_atr_ratio (0.05) must be less than max_atr_ratio (0.01)" in str(
            exc_info.value
        )

    def test_volatility_filter_does_not_mutate_input(
        self, filter_instance, sample_stock
    ):
        """VolatilityFilter does not mutate the original input list."""
        original_stocks = [sample_stock.copy(), sample_stock.copy()]
        original_length = len(original_stocks)
        original_first_atr = original_stocks[0]["atr_14"]

        result = filter_instance.apply(original_stocks)

        # Verify original list is unchanged
        assert len(original_stocks) == original_length
        assert original_stocks[0]["atr_14"] == original_first_atr
        assert id(result) != id(original_stocks)  # Different objects
