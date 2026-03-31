from uuid import UUID


class EncryptionConfigError(Exception):
    """Raised when encryption key is missing or invalid."""
    pass


class InvalidAPIKeyError(Exception):
    """Raised when API key fails validation."""
    def __init__(self, reason: str):
        super().__init__(
            f"API key validation failed: {reason}"
        )


class UserNotFoundError(Exception):
    def __init__(self, user_id: UUID):
        super().__init__(f"User {user_id} not found")

