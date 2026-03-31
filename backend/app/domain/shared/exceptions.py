"""
Base exception hierarchy for pavlov domain errors.
All domain exceptions must inherit from PavlovBaseException.
"""


class PavlovBaseException(Exception):
    """Base exception for all pavlov domain errors."""

    def __init__(
        self,
        message: str,
        code: str = "PAVLOV_ERROR",
        details: dict | None = None,
    ):
        self.code = code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": str(self),
            "details": self.details,
        }


class ExternalServiceError(PavlovBaseException):
    """External API/service failures."""

    def __init__(
        self,
        service: str,
        reason: str,
        details: dict | None = None,
    ):
        super().__init__(
            f"{service} failed: {reason}",
            code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, **(details or {})}
        )


class DataValidationError(PavlovBaseException):
    """Data fails validation rules."""

    def __init__(
        self,
        field: str,
        reason: str,
        value: str | None = None,
    ):
        super().__init__(
            f"Validation failed for {field}: {reason}",
            code="DATA_VALIDATION_ERROR",
            details={"field": field, "value": str(value)}
        )


class SchedulerError(PavlovBaseException):
    """Scheduler job failures."""

    def __init__(self, job_name: str, reason: str):
        super().__init__(
            f"Scheduler job '{job_name}' failed: {reason}",
            code="SCHEDULER_ERROR",
            details={"job": job_name}
        )


class DatabaseError(PavlovBaseException):
    """Database connectivity or query failures."""

    def __init__(self, operation: str, reason: str):
        super().__init__(
            f"Database error during {operation}: {reason}",
            code="DATABASE_ERROR",
            details={"operation": operation}
        )


class ConfigurationError(PavlovBaseException):
    """Missing or invalid configuration."""

    def __init__(self, key: str, reason: str):
        super().__init__(
            f"Configuration error for '{key}': {reason}",
            code="CONFIGURATION_ERROR",
            details={"key": key}
        )
