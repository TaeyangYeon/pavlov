"""
NotificationRepository implementation.
Handles database operations for notifications.
"""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.notification.schemas import NotificationCreate
from app.infra.db.models.notification import Notification, NotificationTypeEnum


class NotificationRepository:
    """Repository for notification database operations."""
    
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, data: NotificationCreate) -> Notification:
        """
        Save a new notification to the database.
        
        Args:
            data: Notification creation data
            
        Returns:
            Notification: The saved notification entity
        """
        row = Notification(
            user_id=data.user_id,
            type=data.type,
            title=data.title,
            body=data.body,
            ticker=data.ticker,
            action=data.action,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return row

    async def get_unread(
        self,
        user_id: UUID | None = None,
        limit: int = 20
    ) -> list[Notification]:
        """
        Get unread notifications, optionally filtered by user.
        
        Args:
            user_id: Filter by user ID (None for all users)
            limit: Maximum number of notifications to return
            
        Returns:
            list[Notification]: List of unread notifications
        """
        stmt = (
            select(Notification)
            .where(Notification.is_read == False)  # noqa: E712
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        if user_id:
            stmt = stmt.where(Notification.user_id == user_id)
            
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def mark_read(self, notification_id: UUID) -> bool:
        """
        Mark a notification as read.
        
        Args:
            notification_id: ID of the notification to mark as read
            
        Returns:
            bool: True if notification was found and marked, False otherwise
        """
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id)
            .values(is_read=True)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount > 0

    async def mark_all_read(self, user_id: UUID | None = None) -> int:
        """
        Mark all unread notifications as read, optionally filtered by user.
        
        Args:
            user_id: Filter by user ID (None for all users)
            
        Returns:
            int: Number of notifications marked as read
        """
        stmt = (
            update(Notification)
            .where(Notification.is_read == False)  # noqa: E712
            .values(is_read=True)
        )
        if user_id:
            stmt = stmt.where(Notification.user_id == user_id)
            
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount

    async def get_latest_strategy_alert(self, ticker: str) -> Notification | None:
        """
        Get the most recent strategy_change notification for a ticker.
        Used for cooling-off period checks.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Notification | None: Latest strategy alert or None if not found
        """
        stmt = (
            select(Notification)
            .where(
                Notification.ticker == ticker,
                Notification.type == NotificationTypeEnum.STRATEGY_CHANGE,
            )
            .order_by(Notification.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()