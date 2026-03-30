"""
Notification domain interfaces.
Abstract base classes for notification ports (channels).
"""

from abc import ABC, abstractmethod

from .schemas import NotificationCreate


class NotificationPort(ABC):
    """
    Abstract base class for notification channels.
    
    This allows NotificationService to depend on abstractions
    rather than concrete implementations, enabling easy addition
    of new notification channels without modifying the service.
    """
    
    @abstractmethod
    async def send(self, notification: NotificationCreate) -> bool:
        """
        Send a notification through this channel.
        
        Args:
            notification: The notification to send
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def channel_name(self) -> str:
        """
        Get the name of this notification channel.
        
        Returns:
            str: Channel name (e.g., "in_app", "email", "sms")
        """
        pass