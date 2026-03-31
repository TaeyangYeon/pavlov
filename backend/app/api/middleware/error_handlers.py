"""
Global FastAPI error handlers for structured error responses.
"""

import traceback
import uuid

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.domain.shared.exceptions import (
    ConfigurationError,
    DatabaseError,
    DataValidationError,
    ExternalServiceError,
    PavlovBaseException,
    SchedulerError,
)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for global error handling and logging.
    Adds correlation IDs and request context to all errors.
    """

    async def dispatch(self, request: Request, call_next):
        # Generate correlation ID for this request
        correlation_id = str(uuid.uuid4())

        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Log the error with context
            error_context = {
                "correlation_id": correlation_id,
                "request_path": str(request.url.path),
                "request_method": request.method,
                "exception_type": type(exc).__name__,
                "user_agent": request.headers.get("user-agent", "unknown")
            }

            # TODO: Replace with proper structured logging
            print(f"[ERROR] {correlation_id}: {str(exc)} - Context: {error_context}")

            # Handle different exception types
            if isinstance(exc, PavlovBaseException):
                return await handle_pavlov_exception(exc, correlation_id)
            elif isinstance(exc, HTTPException):
                return await handle_http_exception(exc, correlation_id)
            else:
                return await handle_unexpected_exception(exc, correlation_id)


async def handle_pavlov_exception(exc: PavlovBaseException, correlation_id: str) -> JSONResponse:
    """Handle Pavlov domain exceptions with structured response."""

    # Determine HTTP status code based on exception type
    if isinstance(exc, ConfigurationError):
        status_code = 500  # Internal Server Error
    elif isinstance(exc, DatabaseError):
        status_code = 503  # Service Unavailable
    elif isinstance(exc, ExternalServiceError):
        status_code = 502  # Bad Gateway
    elif isinstance(exc, DataValidationError):
        status_code = 400  # Bad Request
    elif isinstance(exc, SchedulerError):
        status_code = 500  # Internal Server Error
    else:
        status_code = 500  # Default to Internal Server Error

    # Sanitize sensitive information for database errors
    error_message = str(exc)
    error_details = exc.details.copy() if exc.details else {}

    if isinstance(exc, DatabaseError):
        # Hide sensitive database connection details
        error_message = f"Database operation '{error_details.get('operation', 'unknown')}' failed"
        error_details = {"operation": error_details.get("operation", "unknown")}

    error_response = {
        "error": {
            "code": exc.code,
            "message": error_message,
            "type": type(exc).__name__,
            "details": error_details,
            "correlation_id": correlation_id
        }
    }

    return JSONResponse(
        status_code=status_code,
        content=error_response,
        headers={"X-Correlation-ID": correlation_id}
    )


async def handle_http_exception(exc: HTTPException, correlation_id: str) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    error_response = {
        "error": {
            "code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "type": "HTTPException",
            "details": {"status_code": exc.status_code},
            "correlation_id": correlation_id
        }
    }

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers={"X-Correlation-ID": correlation_id}
    )


async def handle_unexpected_exception(exc: Exception, correlation_id: str) -> JSONResponse:
    """Handle unexpected exceptions that escape domain layer."""

    # Log full traceback for debugging (only in development)
    # TODO: Add proper logging configuration check
    print(f"[CRITICAL] Unexpected exception {correlation_id}: {traceback.format_exc()}")

    # Never expose internal details in production
    error_response = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred",
            "type": "InternalServerError",
            "details": {},
            "correlation_id": correlation_id
        }
    }

    return JSONResponse(
        status_code=500,
        content=error_response,
        headers={"X-Correlation-ID": correlation_id}
    )


def setup_error_handlers(app):
    """
    Set up global error handlers for the FastAPI application.
    """

    @app.exception_handler(PavlovBaseException)
    async def pavlov_exception_handler(request: Request, exc: PavlovBaseException):
        correlation_id = str(uuid.uuid4())
        return await handle_pavlov_exception(exc, correlation_id)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        correlation_id = str(uuid.uuid4())
        return await handle_http_exception(exc, correlation_id)

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        correlation_id = str(uuid.uuid4())

        # If it's a Pavlov exception that wasn't caught by the specific handler
        if isinstance(exc, PavlovBaseException):
            return await handle_pavlov_exception(exc, correlation_id)

        return await handle_unexpected_exception(exc, correlation_id)

    # Add error handling middleware
    app.add_middleware(ErrorHandlingMiddleware)
