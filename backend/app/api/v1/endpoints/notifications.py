"""
Notification API endpoints.
REST endpoints for managing notifications and polling.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.domain.notification.schemas import NotificationResponse
from app.infra.db.repositories.notification_repository import NotificationRepository

router = APIRouter(
    prefix="/notifications", tags=["notifications"]
)


@router.get(
    "/unread",
    response_model=list[NotificationResponse],
    summary="Get unread notifications",
    description="Get unread notifications for short-polling. Frontend polls every 30 seconds."
)
async def get_unread_notifications(
    limit: int = Query(default=20, le=50, description="Maximum notifications to return"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get unread notifications (short-polling endpoint).
    Frontend polls every 30 seconds.
    """
    repo = NotificationRepository(session)
    rows = await repo.get_unread(limit=limit)
    
    return [
        NotificationResponse(
            id=r.id,
            type=r.type.value,
            title=r.title,
            body=r.body,
            ticker=r.ticker,
            action=r.action,
            is_read=r.is_read,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.patch(
    "/{notification_id}/read",
    summary="Mark notification as read",
    description="Mark a specific notification as read"
)
async def mark_notification_read(
    notification_id: UUID,
    session: AsyncSession = Depends(get_db_session),
):
    """Mark a specific notification as read."""
    repo = NotificationRepository(session)
    success = await repo.mark_read(notification_id)
    
    if not success:
        raise HTTPException(
            status_code=404, 
            detail="Notification not found"
        )
    
    return {"message": "Marked as read"}


@router.patch(
    "/read-all",
    summary="Mark all notifications as read",
    description="Mark all unread notifications as read"
)
async def mark_all_notifications_read(
    session: AsyncSession = Depends(get_db_session),
):
    """Mark all unread notifications as read."""
    repo = NotificationRepository(session)
    count = await repo.mark_all_read()
    
    return {"marked_read": count}