"""
Unit tests for base exception hierarchy and Result[T] monad.
"""

import pytest
from app.domain.shared.exceptions import (
    PavlovBaseException,
    ExternalServiceError,
    DataValidationError,
    SchedulerError,
    DatabaseError,
    ConfigurationError,
)
from app.domain.shared.result import Result


class TestPavlovBaseException:
    """Test base exception functionality."""

    def test_pavlov_exception_has_code(self):
        exc = PavlovBaseException("test message", "TEST_CODE")
        assert exc.code == "TEST_CODE"

    def test_pavlov_exception_to_dict(self):
        exc = PavlovBaseException(
            "test message",
            "TEST_CODE",
            {"key": "value"}
        )
        result = exc.to_dict()
        
        assert "code" in result
        assert "message" in result
        assert "details" in result
        assert result["code"] == "TEST_CODE"
        assert result["message"] == "test message"
        assert result["details"]["key"] == "value"


class TestSpecificExceptions:
    """Test specific exception types."""

    def test_external_service_error_inherits_base(self):
        exc = ExternalServiceError("test_service", "connection failed")
        assert isinstance(exc, PavlovBaseException)

    def test_external_service_error_sets_service_details(self):
        exc = ExternalServiceError("test_service", "connection failed")
        assert exc.details["service"] == "test_service"

    def test_data_validation_error_has_field(self):
        exc = DataValidationError("price", "negative value", "-5")
        assert exc.details["field"] == "price"
        assert exc.details["value"] == "-5"

    def test_scheduler_error_has_job_name(self):
        exc = SchedulerError("test_job", "timeout")
        assert exc.details["job"] == "test_job"

    def test_database_error_has_operation(self):
        exc = DatabaseError("startup_check", "connection refused")
        assert exc.details["operation"] == "startup_check"

    def test_configuration_error_has_key(self):
        exc = ConfigurationError("api_key", "missing value")
        assert exc.details["key"] == "api_key"


class TestResultMonad:
    """Test Result[T] monad functionality."""

    def test_result_ok_returns_value(self):
        result = Result.ok(42)
        assert result.unwrap() == 42
        assert result.is_ok()
        assert not result.is_err()

    def test_result_fail_returns_error(self):
        result = Result.fail("network error")
        assert result.success == False
        assert result.error == "network error"
        assert not result.is_ok()
        assert result.is_err()

    def test_result_unwrap_raises_on_failure(self):
        result = Result.fail("test error")
        with pytest.raises(ValueError, match="test error"):
            result.unwrap()

    def test_result_unwrap_or_returns_default(self):
        result = Result.fail("test error")
        assert result.unwrap_or(0) == 0

    def test_result_unwrap_or_returns_value_on_success(self):
        result = Result.ok(42)
        assert result.unwrap_or(0) == 42

    def test_result_map_transforms_value(self):
        result = Result.ok(5)
        transformed = result.map(lambda x: x * 2)
        assert transformed.unwrap() == 10

    def test_result_map_preserves_failure(self):
        result = Result.fail("original error")
        transformed = result.map(lambda x: x * 2)
        assert transformed.is_err()
        assert transformed.error == "original error"

    def test_result_map_catches_transform_exception(self):
        result = Result.ok(5)
        transformed = result.map(lambda x: x / 0)  # Division by zero
        assert transformed.is_err()
        assert "division by zero" in transformed.error.lower()

    def test_result_none_value_unwrap_raises(self):
        # Edge case: success=True but value=None
        result = Result(value=None, error=None, success=True)
        with pytest.raises(ValueError):
            result.unwrap()

    def test_result_none_value_unwrap_or_returns_default(self):
        result = Result(value=None, error=None, success=False)
        assert result.unwrap_or("default") == "default"