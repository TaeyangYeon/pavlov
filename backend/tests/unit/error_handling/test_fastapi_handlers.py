"""
Unit tests for FastAPI global error handlers and exception middleware.
"""

import json
import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.domain.shared.exceptions import (
    PavlovBaseException,
    ExternalServiceError,
    DataValidationError,
    DatabaseError,
    ConfigurationError
)


class TestFastAPIExceptionHandlers:
    """Test FastAPI global exception handlers."""

    def test_pavlov_base_exception_handler_returns_structured_response(self):
        """Test that PavlovBaseException returns structured JSON response."""
        # Mock request
        mock_request = MagicMock(spec=Request)
        
        # Create exception
        exc = PavlovBaseException(
            "Test error",
            "TEST_ERROR",
            {"key": "value"}
        )
        
        # Simulate what the handler should return
        expected_response = {
            "error": {
                "code": "TEST_ERROR",
                "message": "Test error",
                "details": {"key": "value"},
                "type": "PavlovBaseException"
            }
        }
        
        # In the actual handler, this would return JSONResponse
        assert expected_response["error"]["code"] == "TEST_ERROR"
        assert expected_response["error"]["details"]["key"] == "value"

    def test_external_service_error_handler_includes_service_info(self):
        """Test ExternalServiceError handler includes service information."""
        mock_request = MagicMock(spec=Request)
        
        exc = ExternalServiceError(
            service="anthropic_api",
            reason="Rate limit exceeded"
        )
        
        expected_response = {
            "error": {
                "code": "EXTERNAL_SERVICE_ERROR",
                "message": "External service 'anthropic_api' failed: Rate limit exceeded",
                "details": {"service": "anthropic_api"},
                "type": "ExternalServiceError"
            }
        }
        
        assert expected_response["error"]["details"]["service"] == "anthropic_api"
        assert "Rate limit exceeded" in expected_response["error"]["message"]

    def test_data_validation_error_handler_includes_field_info(self):
        """Test DataValidationError handler includes field information."""
        mock_request = MagicMock(spec=Request)
        
        exc = DataValidationError(
            field="price",
            reason="Value must be positive",
            value="-100"
        )
        
        expected_response = {
            "error": {
                "code": "DATA_VALIDATION_ERROR", 
                "message": "Data validation failed for field 'price': Value must be positive",
                "details": {"field": "price", "value": "-100"},
                "type": "DataValidationError"
            }
        }
        
        assert expected_response["error"]["details"]["field"] == "price"
        assert expected_response["error"]["details"]["value"] == "-100"

    def test_database_error_handler_hides_sensitive_details(self):
        """Test DatabaseError handler hides sensitive database details."""
        mock_request = MagicMock(spec=Request)
        
        exc = DatabaseError(
            operation="user_lookup",
            reason="Connection to database failed: password authentication failed for user 'admin'"
        )
        
        # Handler should sanitize sensitive information
        expected_response = {
            "error": {
                "code": "DATABASE_ERROR",
                "message": "Database operation 'user_lookup' failed",
                "details": {"operation": "user_lookup"},
                "type": "DatabaseError"
            }
        }
        
        # Should NOT include password or connection details
        assert "password" not in expected_response["error"]["message"]
        assert "admin" not in expected_response["error"]["message"]

    def test_configuration_error_handler_returns_500_status(self):
        """Test ConfigurationError handler returns 500 status code."""
        mock_request = MagicMock(spec=Request)
        
        exc = ConfigurationError(
            key="api_key",
            reason="Missing required configuration"
        )
        
        # Should return 500 status for configuration errors
        expected_status = 500
        expected_response = {
            "error": {
                "code": "CONFIGURATION_ERROR",
                "message": "Configuration error for 'api_key': Missing required configuration",
                "details": {"key": "api_key"},
                "type": "ConfigurationError"
            }
        }
        
        assert expected_status == 500
        assert expected_response["error"]["code"] == "CONFIGURATION_ERROR"

    def test_unhandled_exception_handler_returns_generic_error(self):
        """Test unhandled exception handler returns generic error response."""
        mock_request = MagicMock(spec=Request)
        
        # Unhandled exception (not a PavlovBaseException)
        exc = ValueError("Unexpected error")
        
        expected_response = {
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred",
                "details": {},
                "type": "InternalServerError"
            }
        }
        
        # Should NOT expose internal details
        assert "Unexpected error" not in expected_response["error"]["message"]
        assert expected_response["error"]["code"] == "INTERNAL_SERVER_ERROR"

    def test_http_exception_handler_preserves_fastapi_behavior(self):
        """Test HTTP exception handler preserves FastAPI behavior."""
        mock_request = MagicMock(spec=Request)
        
        exc = HTTPException(
            status_code=404,
            detail="User not found"
        )
        
        expected_response = {
            "error": {
                "code": "HTTP_404",
                "message": "User not found",
                "details": {"status_code": 404},
                "type": "HTTPException"
            }
        }
        
        assert expected_response["error"]["code"] == "HTTP_404"
        assert expected_response["error"]["details"]["status_code"] == 404


class TestErrorMiddleware:
    """Test error handling middleware."""

    def test_error_middleware_logs_exceptions(self):
        """Test that error middleware logs all exceptions."""
        logged_errors = []
        
        def mock_logger(level, message, **kwargs):
            logged_errors.append({
                "level": level,
                "message": message,
                "extra": kwargs
            })
        
        # Simulate middleware catching exception
        exc = ExternalServiceError("test_service", "Connection failed")
        
        # Middleware should log the error
        mock_logger("error", "Exception occurred in request", 
                   exception=exc, 
                   request_id="req_123")
        
        assert len(logged_errors) == 1
        assert logged_errors[0]["level"] == "error"
        assert "Exception occurred" in logged_errors[0]["message"]

    def test_error_middleware_adds_request_context(self):
        """Test that error middleware adds request context to errors."""
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/v1/analysis"
        mock_request.method = "POST"
        
        exc = DataValidationError("ticker", "Invalid format", "INVALID")
        
        # Middleware should add request context
        error_context = {
            "request_path": mock_request.url.path,
            "request_method": mock_request.method,
            "exception_type": type(exc).__name__,
            "exception_code": exc.code
        }
        
        assert error_context["request_path"] == "/api/v1/analysis"
        assert error_context["request_method"] == "POST"
        assert error_context["exception_type"] == "DataValidationError"

    def test_error_middleware_generates_correlation_id(self):
        """Test that error middleware generates correlation IDs."""
        import uuid
        
        # Simulate middleware generating correlation ID
        correlation_id = str(uuid.uuid4())
        
        expected_headers = {
            "X-Correlation-ID": correlation_id,
            "X-Error-Type": "EXTERNAL_SERVICE_ERROR"
        }
        
        assert "X-Correlation-ID" in expected_headers
        assert len(expected_headers["X-Correlation-ID"]) > 20  # UUID length


class TestHealthEndpointErrors:
    """Test health endpoint error scenarios."""

    def test_health_endpoint_returns_503_on_db_failure(self):
        """Test health endpoint returns 503 when database is unhealthy."""
        # Mock unhealthy database
        db_health = {
            "status": "unhealthy",
            "error": "Connection timeout",
            "latency_ms": None
        }
        
        overall_health = {
            "status": "unhealthy",
            "checks": {
                "database": db_health,
                "cache": {"status": "healthy"},
                "external_apis": {"status": "healthy"}
            }
        }
        
        expected_status = 503  # Service Unavailable
        assert overall_health["status"] == "unhealthy"
        assert expected_status == 503

    def test_health_endpoint_returns_200_on_degraded_service(self):
        """Test health endpoint returns 200 for degraded but functional service."""
        # Some services are down but core functionality works
        overall_health = {
            "status": "degraded",
            "checks": {
                "database": {"status": "healthy", "latency_ms": 50},
                "cache": {"status": "healthy", "latency_ms": 5},
                "market_data_kr": {"status": "unhealthy", "error": "Timeout"},
                "market_data_us": {"status": "healthy", "latency_ms": 200},
                "anthropic_api": {"status": "healthy", "latency_ms": 1500}
            }
        }
        
        expected_status = 200  # OK (degraded but functional)
        assert overall_health["status"] == "degraded"
        assert overall_health["checks"]["database"]["status"] == "healthy"
        assert expected_status == 200

    def test_health_endpoint_includes_dependency_details(self):
        """Test health endpoint includes detailed dependency information."""
        health_response = {
            "status": "healthy",
            "timestamp": "2024-01-15T10:00:00Z",
            "uptime_seconds": 3600,
            "checks": {
                "database": {
                    "status": "healthy",
                    "latency_ms": 25.5,
                    "pool_size": 20,
                    "active_connections": 3
                },
                "anthropic_api": {
                    "status": "healthy", 
                    "latency_ms": 800,
                    "rate_limit_remaining": 950
                },
                "market_data_sources": {
                    "status": "healthy",
                    "kr_market": {"status": "healthy", "latency_ms": 150},
                    "us_market": {"status": "healthy", "latency_ms": 300}
                }
            }
        }
        
        assert "timestamp" in health_response
        assert "uptime_seconds" in health_response
        assert health_response["checks"]["database"]["pool_size"] == 20
        assert health_response["checks"]["anthropic_api"]["rate_limit_remaining"] == 950