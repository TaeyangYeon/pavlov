"""AI-specific exceptions for error handling."""

from app.domain.shared.exceptions import (
    ConfigurationError,
    ExternalServiceError,
    DataValidationError,
)


class AIConfigError(ConfigurationError):
    """Raised when AI client is misconfigured (e.g. missing key)."""

    def __init__(self, reason: str):
        super().__init__(key="ai_client", reason=reason)


class AICallError(ExternalServiceError):
    """Raised when AI API call fails after all retries."""

    def __init__(self, attempts: int, last_error: str):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            service="anthropic_api",
            reason=f"Failed after {attempts} attempts: {last_error}",
            details={"attempts": attempts, "last_error": last_error}
        )


class AIResponseParseError(DataValidationError):
    """Raised when AI response cannot be parsed or validated."""

    def __init__(self, reason: str, raw_response: str = ""):
        self.reason = reason
        self.raw_response = raw_response
        super().__init__(
            field="ai_response",
            reason=reason,
            value=raw_response[:100] if raw_response else None
        )

