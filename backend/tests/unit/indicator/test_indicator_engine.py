"""
Unit tests for IndicatorEngine.
Tests orchestration of all 4 indicators and output format.
"""

from unittest.mock import MagicMock

import pytest
from app.domain.ai.schemas import StockIndicators
from app.domain.indicator.engine import IndicatorEngine
from app.domain.indicator.exceptions import InsufficientDataError


class TestIndicatorEngine:
    """Test indicator engine orchestration and output format."""

    @pytest.fixture
    def engine(self):
        """Indicator engine instance."""
        return IndicatorEngine()

    @pytest.fixture
    def complete_data(self):
        """Complete 70 candles for all indicators."""
        return [
            {
                "ticker": "AAPL",
                "market": "US",
                "date": f"2024-01-{i+1:02d}",
                "open": 100.0 + i * 0.1,
                "high": 101.0 + i * 0.1,
                "low": 99.0 + i * 0.1,
                "close": 100.0 + i * 0.1,
                "volume": 1000000 + i * 10000,
            }
            for i in range(70)
        ]

    @pytest.fixture
    def mock_engine_with_indicators(self):
        """Engine with mocked indicators for isolation testing."""
        engine = IndicatorEngine()

        # Mock all indicators
        mock_rsi = MagicMock()
        mock_rsi.indicator_name = "rsi_14"
        mock_rsi.calculate.return_value = {"rsi_14": 65.0}

        mock_ma = MagicMock()
        mock_ma.indicator_name = "moving_average"
        mock_ma.calculate.return_value = {"ma_20": 145.0, "ma_60": 140.0}

        mock_atr = MagicMock()
        mock_atr.indicator_name = "atr_14"
        mock_atr.calculate.return_value = {"atr_14": 2.5}

        mock_vol = MagicMock()
        mock_vol.indicator_name = "volume_ratio"
        mock_vol.calculate.return_value = {"volume_ratio": 1.5}

        engine._indicators = [mock_rsi, mock_ma, mock_atr, mock_vol]
        return engine, mock_rsi, mock_ma, mock_atr, mock_vol

    def test_engine_returns_stock_indicators_dict(
        self, mock_engine_with_indicators, complete_data
    ):
        """Engine should return dict matching StockIndicators schema."""
        engine, _, _, _, _ = mock_engine_with_indicators

        result = engine.calculate_all(
            ticker="AAPL",
            name="Apple Inc.",
            market="NASDAQ",
            ohlcv_data=complete_data,
        )

        # Check all required fields are present
        expected_keys = {
            "ticker",
            "name",
            "market",
            "close",
            "rsi_14",
            "ma_20",
            "ma_60",
            "atr_14",
            "volume_ratio",
        }
        assert set(result.keys()) == expected_keys

        # Check basic values
        assert result["ticker"] == "AAPL"
        assert result["name"] == "Apple Inc."
        assert result["market"] == "NASDAQ"
        assert result["close"] == complete_data[-1]["close"]

    def test_engine_calls_all_four_indicators(
        self, mock_engine_with_indicators, complete_data
    ):
        """Engine should call calculate() on all 4 indicators."""
        engine, mock_rsi, mock_ma, mock_atr, mock_vol = mock_engine_with_indicators

        engine.calculate_all(
            ticker="AAPL",
            name="Apple Inc.",
            market="NASDAQ",
            ohlcv_data=complete_data,
        )

        # Verify all indicators were called
        mock_rsi.calculate.assert_called_once_with(complete_data)
        mock_ma.calculate.assert_called_once_with(complete_data)
        mock_atr.calculate.assert_called_once_with(complete_data)
        mock_vol.calculate.assert_called_once_with(complete_data)

    def test_engine_raises_on_insufficient_data(self, mock_engine_with_indicators):
        """Engine should propagate InsufficientDataError from indicators."""
        engine, mock_rsi, _, _, _ = mock_engine_with_indicators

        # Mock RSI to raise InsufficientDataError
        mock_rsi.calculate.side_effect = InsufficientDataError("rsi_14", 15, 10)

        insufficient_data = [{"close": 100.0}] * 10

        with pytest.raises(InsufficientDataError) as exc_info:
            engine.calculate_all(
                ticker="TEST",
                name="Test Corp",
                market="NYSE",
                ohlcv_data=insufficient_data,
            )

        assert exc_info.value.indicator_name == "rsi_14"
        assert exc_info.value.required == 15
        assert exc_info.value.actual == 10

    def test_engine_output_matches_ai_schema(self, complete_data):
        """Engine output should be valid StockIndicators pydantic model."""
        engine = IndicatorEngine()

        result = engine.calculate_all(
            ticker="AAPL",
            name="Apple Inc.",
            market="NASDAQ",
            ohlcv_data=complete_data,
        )

        # Should not raise ValidationError
        stock_indicators = StockIndicators(**result)

        # Verify some basic constraints
        assert 0 <= stock_indicators.rsi_14 <= 100
        assert stock_indicators.volume_ratio > 0
        assert stock_indicators.ma_20 > 0
        assert stock_indicators.ma_60 > 0
        assert stock_indicators.atr_14 > 0

    def test_engine_ticker_and_name_preserved(self, complete_data):
        """Engine should preserve ticker and name exactly as passed."""
        engine = IndicatorEngine()

        result = engine.calculate_all(
            ticker="CUSTOM",
            name="Custom Company Ltd.",
            market="NASDAQ",
            ohlcv_data=complete_data,
        )

        assert result["ticker"] == "CUSTOM"
        assert result["name"] == "Custom Company Ltd."
        assert result["market"] == "NASDAQ"
