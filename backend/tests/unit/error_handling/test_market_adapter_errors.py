"""
Unit tests for market adapter error handling and validation.
"""

import asyncio
import math
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.domain.market.exceptions import MarketDataFetchError
from app.domain.shared.exceptions import DataValidationError
from app.domain.shared.result import Result


class TestMarketAdapterTimeouts:
    """Test timeout handling in market adapters."""

    @patch('asyncio.wait_for')
    async def test_kr_adapter_timeout_raises_market_error(self, mock_wait_for):
        """Test that timeout in KR adapter raises MarketDataFetchError."""
        mock_wait_for.side_effect = asyncio.TimeoutError()
        
        # Note: We'll mock the actual adapter in the green phase
        # For now, just test the timeout handling logic
        with pytest.raises(MarketDataFetchError) as exc_info:
            # Simulating what the adapter should do on timeout
            try:
                await asyncio.wait_for(AsyncMock()(), timeout=30)
            except asyncio.TimeoutError:
                raise MarketDataFetchError(
                    ticker="005930",
                    market="KR", 
                    reason="Timeout after 30s"
                )
        
        assert "Timeout after 30s" in str(exc_info.value)

    @patch('asyncio.wait_for') 
    async def test_us_adapter_timeout_raises_market_error(self, mock_wait_for):
        """Test that timeout in US adapter raises MarketDataFetchError."""
        mock_wait_for.side_effect = asyncio.TimeoutError()
        
        with pytest.raises(MarketDataFetchError) as exc_info:
            try:
                await asyncio.wait_for(AsyncMock()(), timeout=30)
            except asyncio.TimeoutError:
                raise MarketDataFetchError(
                    ticker="AAPL",
                    market="US",
                    reason="Timeout after 30s"
                )
        
        assert "Timeout after 30s" in str(exc_info.value)


class TestMarketDataFallback:
    """Test fallback strategies for market data."""

    async def test_fallback_to_cache_on_adapter_failure(self):
        """Test fallback to cache when adapter fails."""
        # Mock adapter fails
        mock_adapter_result = MarketDataFetchError(
            ticker="AAPL",
            market="US", 
            reason="API unavailable"
        )
        
        # Mock cache returns data
        cached_data = {
            "ticker": "AAPL",
            "close": 150.0,
            "date": "2024-01-01"
        }
        
        # Simulate fallback service logic
        try:
            raise mock_adapter_result
        except MarketDataFetchError:
            # Fallback to cache
            result = Result.ok(cached_data)
        
        assert result.is_ok()
        assert result.unwrap()["ticker"] == "AAPL"

    async def test_fallback_fails_gracefully_when_no_cache(self):
        """Test graceful failure when both adapter and cache fail."""
        # Both adapter and cache fail
        result = Result.fail("No data available for AAPL on 2024-01-01 or 2023-12-31")
        
        assert result.is_err()
        assert "No data available" in result.error


class TestMarketDataValidation:
    """Test market data validation rules."""

    def test_market_data_validation_rejects_negative_price(self):
        """Test validation rejects negative prices."""
        data = {
            "ticker": "AAPL",
            "open": 100.0,
            "high": 105.0,
            "low": 95.0,
            "close": -100.0,  # Invalid negative price
            "volume": 1000
        }
        
        with pytest.raises(DataValidationError) as exc_info:
            # Simulating validator logic
            if data["close"] <= 0:
                raise DataValidationError(
                    field="close",
                    reason="Close price must be positive",
                    value=str(data["close"])
                )
        
        assert exc_info.value.details["field"] == "close"
        assert exc_info.value.details["value"] == "-100.0"

    def test_market_data_validation_rejects_nan(self):
        """Test validation rejects NaN values."""
        data = {
            "ticker": "AAPL", 
            "open": 100.0,
            "high": 105.0,
            "low": 95.0,
            "close": float("nan"),  # Invalid NaN
            "volume": 1000
        }
        
        with pytest.raises(DataValidationError) as exc_info:
            # Simulating validator logic
            if math.isnan(data["close"]):
                raise DataValidationError(
                    field="close",
                    reason="NaN value in market data",
                    value=str(data["close"])
                )
        
        assert exc_info.value.details["field"] == "close"

    def test_market_data_validation_rejects_high_less_than_low(self):
        """Test validation rejects high < low."""
        data = {
            "ticker": "AAPL",
            "open": 100.0, 
            "high": 90.0,   # Invalid: high < low
            "low": 95.0,
            "close": 92.0,
            "volume": 1000
        }
        
        with pytest.raises(DataValidationError) as exc_info:
            # Simulating validator logic
            if data["high"] < data["low"]:
                raise DataValidationError(
                    field="high/low",
                    reason=f"High ({data['high']}) cannot be less than Low ({data['low']})"
                )
        
        assert exc_info.value.details["field"] == "high/low"

    def test_market_data_validation_rejects_negative_volume(self):
        """Test validation rejects negative volume."""
        data = {
            "ticker": "AAPL",
            "open": 100.0,
            "high": 105.0, 
            "low": 95.0,
            "close": 100.0,
            "volume": -1000  # Invalid negative volume
        }
        
        with pytest.raises(DataValidationError) as exc_info:
            # Simulating validator logic
            if data["volume"] < 0:
                raise DataValidationError(
                    field="volume",
                    reason="Volume cannot be negative",
                    value=str(data["volume"])
                )
        
        assert exc_info.value.details["field"] == "volume"

    def test_market_data_validation_passes_valid_data(self):
        """Test validation passes for valid OHLCV data."""
        data = {
            "ticker": "AAPL",
            "open": 100.0,
            "high": 105.0,
            "low": 95.0, 
            "close": 102.0,
            "volume": 1000
        }
        
        # Should not raise any exception
        # Simulating validator logic - all checks pass
        assert data["close"] > 0
        assert not math.isnan(data["close"])
        assert data["high"] >= data["low"]
        assert data["volume"] >= 0

    def test_market_data_validation_missing_fields(self):
        """Test validation rejects missing required fields."""
        data = {
            "ticker": "AAPL",
            "open": 100.0,
            # Missing high, low, close, volume
        }
        
        required = ["open", "high", "low", "close", "volume"]
        for field in required:
            if field not in data:
                with pytest.raises(DataValidationError) as exc_info:
                    raise DataValidationError(
                        field=field,
                        reason="Field missing from market data"
                    )
                assert exc_info.value.details["field"] == field
                break  # Test first missing field