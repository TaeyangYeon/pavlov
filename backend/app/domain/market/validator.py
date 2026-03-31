"""
Market data validation and sanitization.
Validates OHLCV data for consistency and business rules.
"""

import math
from typing import Any

from app.domain.shared.exceptions import DataValidationError


class MarketDataValidator:
    """
    Validates market data according to business rules.
    
    Rules:
    - All prices must be positive (> 0)
    - High >= Low
    - Volume >= 0
    - No NaN or infinite values
    - Required fields present
    """

    REQUIRED_FIELDS = ["ticker", "open", "high", "low", "close", "volume", "date"]
    PRICE_FIELDS = ["open", "high", "low", "close"]

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate market data and return sanitized version.
        
        Args:
            data: Raw market data dictionary
            
        Returns:
            Validated and sanitized market data
            
        Raises:
            DataValidationError: If validation fails
        """
        if not isinstance(data, dict):
            raise DataValidationError(
                field="data",
                reason="Market data must be a dictionary"
            )

        # Check required fields
        self._validate_required_fields(data)

        # Validate individual fields
        self._validate_ticker(data["ticker"])
        self._validate_prices(data)
        self._validate_volume(data["volume"])
        self._validate_ohlc_consistency(data)

        # Return sanitized copy
        return self._sanitize_data(data)

    def _validate_required_fields(self, data: dict[str, Any]) -> None:
        """Validate all required fields are present."""
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                raise DataValidationError(
                    field=field,
                    reason="Field missing from market data"
                )

    def _validate_ticker(self, ticker: Any) -> None:
        """Validate ticker symbol."""
        if not isinstance(ticker, str) or not ticker.strip():
            raise DataValidationError(
                field="ticker",
                reason="Ticker must be a non-empty string",
                value=str(ticker) if ticker is not None else "None"
            )

    def _validate_prices(self, data: dict[str, Any]) -> None:
        """Validate all price fields."""
        for field in self.PRICE_FIELDS:
            value = data[field]

            # Check for numeric type
            if not isinstance(value, (int, float)):
                raise DataValidationError(
                    field=field,
                    reason="Price must be a number",
                    value=str(value)
                )

            # Check for NaN or infinite
            if math.isnan(value) or math.isinf(value):
                raise DataValidationError(
                    field=field,
                    reason="NaN or infinite value in market data",
                    value=str(value)
                )

            # Check for positive value
            if value <= 0:
                raise DataValidationError(
                    field=field,
                    reason=f"{field.capitalize()} price must be positive",
                    value=str(value)
                )

    def _validate_volume(self, volume: Any) -> None:
        """Validate volume field."""
        if not isinstance(volume, (int, float)):
            raise DataValidationError(
                field="volume",
                reason="Volume must be a number",
                value=str(volume)
            )

        if math.isnan(volume) or math.isinf(volume):
            raise DataValidationError(
                field="volume",
                reason="NaN or infinite value in volume",
                value=str(volume)
            )

        if volume < 0:
            raise DataValidationError(
                field="volume",
                reason="Volume cannot be negative",
                value=str(volume)
            )

    def _validate_ohlc_consistency(self, data: dict[str, Any]) -> None:
        """Validate OHLC price consistency."""
        open_price = data["open"]
        high_price = data["high"]
        low_price = data["low"]
        close_price = data["close"]

        # High must be >= Low
        if high_price < low_price:
            raise DataValidationError(
                field="high/low",
                reason=f"High ({high_price}) cannot be less than Low ({low_price})"
            )

        # High must be >= Open and Close
        if high_price < open_price:
            raise DataValidationError(
                field="high/open",
                reason=f"High ({high_price}) cannot be less than Open ({open_price})"
            )

        if high_price < close_price:
            raise DataValidationError(
                field="high/close",
                reason=f"High ({high_price}) cannot be less than Close ({close_price})"
            )

        # Low must be <= Open and Close
        if low_price > open_price:
            raise DataValidationError(
                field="low/open",
                reason=f"Low ({low_price}) cannot be greater than Open ({open_price})"
            )

        if low_price > close_price:
            raise DataValidationError(
                field="low/close",
                reason=f"Low ({low_price}) cannot be greater than Close ({close_price})"
            )

    def _sanitize_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize data by normalizing values.
        
        - Round prices to 4 decimal places
        - Round volume to integer
        - Strip and uppercase ticker
        """
        sanitized = data.copy()

        # Sanitize ticker
        sanitized["ticker"] = str(data["ticker"]).strip().upper()

        # Round prices to 4 decimal places
        for field in self.PRICE_FIELDS:
            sanitized[field] = round(float(data[field]), 4)

        # Round volume to integer
        sanitized["volume"] = int(round(float(data["volume"])))

        return sanitized

    def validate_multiple(self, data_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Validate multiple market data records.
        
        Args:
            data_list: List of market data dictionaries
            
        Returns:
            List of validated market data
            
        Raises:
            DataValidationError: If any validation fails
        """
        if not isinstance(data_list, list):
            raise DataValidationError(
                field="data_list",
                reason="Market data must be a list"
            )

        validated_list = []
        for i, data in enumerate(data_list):
            try:
                validated_data = self.validate(data)
                validated_list.append(validated_data)
            except DataValidationError as e:
                # Add context about which record failed
                raise DataValidationError(
                    field=f"data_list[{i}].{e.details['field']}",
                    reason=e.details["reason"],
                    value=e.details.get("value")
                )

        return validated_list
