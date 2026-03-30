"""
Email Notifier implementation.
Sends notifications via SMTP email (optional).
"""

import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import Settings
from app.domain.notification.interfaces import NotificationPort
from app.domain.notification.schemas import NotificationCreate


class EmailNotifier(NotificationPort):
    """
    Email notification channel using SMTP.
    
    Only active when EMAIL_ENABLED=true in configuration.
    Failures are non-fatal (log error + return False).
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the email notifier.
        
        Args:
            settings: Application settings with email configuration
        """
        self._settings = settings

    @property
    def channel_name(self) -> str:
        """Get the channel name."""
        return "email"

    async def send(self, notification: NotificationCreate) -> bool:
        """
        Send notification via email.
        
        Args:
            notification: The notification to send
            
        Returns:
            bool: True if sent successfully, False if disabled or failed
        """
        if not self._settings.email_enabled:
            return False
            
        try:
            # Execute synchronous SMTP operations in thread pool
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._send_sync,
                notification
            )
            return True
        except Exception as e:
            # Log error but don't raise - email failure must never block in-app notification
            print(f"[EmailNotifier] Failed to send email: {e}")
            return False

    def _send_sync(self, notification: NotificationCreate) -> None:
        """
        Send email using synchronous SMTP operations.
        
        Args:
            notification: The notification to send
        """
        # Create email message
        msg = MIMEMultipart()
        msg["From"] = self._settings.email_user
        msg["To"] = self._settings.email_to
        msg["Subject"] = f"[pavlov] {notification.title}"
        
        # Attach body
        body = MIMEText(notification.body, "plain")
        msg.attach(body)
        
        # Send via SMTP
        with smtplib.SMTP(self._settings.email_host, self._settings.email_port) as server:
            server.starttls()
            server.login(self._settings.email_user, self._settings.email_password)
            server.send_message(msg)