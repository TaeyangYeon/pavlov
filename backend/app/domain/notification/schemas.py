"""
Notification domain schemas.
Data transfer objects for notification operations.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationCreate(BaseModel):
    """Schema for creating a new notification."""
    
    type: str = Field(description="Notification type")
    title: str = Field(max_length=100, description="Notification title")
    body: str = Field(max_length=500, description="Notification body")
    ticker: str | None = Field(default=None, description="Related ticker symbol")
    action: str | None = Field(default=None, description="Related action")
    user_id: UUID | None = Field(default=None, description="Target user ID (stub for now)")


class NotificationResponse(BaseModel):
    """Schema for notification API responses."""
    
    id: UUID
    type: str
    title: str
    body: str
    ticker: str | None
    action: str | None
    is_read: bool
    created_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}