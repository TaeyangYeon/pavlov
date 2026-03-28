"""AI-specific exceptions for error handling."""


class AIConfigError(Exception):
    """Raised when AI client is misconfigured (e.g. missing key)."""

    pass


class AICallError(Exception):
    """Raised when AI API call fails after all retries."""

    def __init__(self, attempts: int, last_error: str):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            f"AI call failed after {attempts} attempts. "
            f"Last error: {last_error}"
        )


class AIResponseParseError(Exception):
    """Raised when AI response cannot be parsed or validated."""

    def __init__(self, reason: str, raw_response: str = ""):
        self.reason = reason
        self.raw_response = raw_response
        super().__init__(f"Failed to parse AI response: {reason}")

