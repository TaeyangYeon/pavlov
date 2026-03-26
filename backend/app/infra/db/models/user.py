from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Boolean, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as SQLAlchemyUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class User(Base):
    """User model for authentication and preferences."""
    
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # User authentication
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    # API key storage (encrypted in Step 19)
    # TODO Step 19: Implement actual encryption for api_key_encrypted field
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # User preferences and settings
    preferences: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, is_active={self.is_active})>"