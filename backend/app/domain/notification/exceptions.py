"""
Notification domain exceptions.
Business logic related exceptions for notification operations.
"""


class NotificationError(Exception):
    """Base exception for notification operations."""
    pass


class NotificationNotFoundError(NotificationError):
    """Raised when a notification is not found."""
    pass


class NotificationSendError(NotificationError):
    """Raised when notification sending fails."""
    pass