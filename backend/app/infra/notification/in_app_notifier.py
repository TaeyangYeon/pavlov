"""
In-App Notifier implementation.
Stores notifications in database for frontend polling.
"""

from app.domain.notification.interfaces import NotificationPort
from app.domain.notification.schemas import NotificationCreate
from app.infra.db.repositories.notification_repository import NotificationRepository


class InAppNotifier(NotificationPort):
    """
    In-app notification channel that stores notifications in database.
    
    Single responsibility: DB persistence only.
    Frontend polls the API to retrieve unread notifications.
    """
    
    def __init__(self, repository: NotificationRepository):
        """
        Initialize the in-app notifier.
        
        Args:
            repository: NotificationRepository for database operations
        """
        self._repository = repository

    @property
    def channel_name(self) -> str:
        """Get the channel name."""
        return "in_app"

    async def send(self, notification: NotificationCreate) -> bool:
        """
        Send notification by saving to database.
        
        Args:
            notification: The notification to save
            
        Returns:
            bool: True if saved successfully, False if error occurred
        """
        try:
            await self._repository.save(notification)
            return True
        except Exception as e:
            # Log error but don't raise - notification failures should not block the system
            print(f"[InAppNotifier] Failed to save notification: {e}")
            return False