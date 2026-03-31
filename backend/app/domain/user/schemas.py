from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)


class UserResponse(BaseModel):
    id: UUID
    email: str
    has_api_key: bool  # True if api_key_encrypted is set
    is_active: bool
    created_at: datetime


class APIKeySetRequest(BaseModel):
    api_key: str = Field(
        min_length=10,
        description="Anthropic API key"
    )


class APIKeySetResponse(BaseModel):
    success: bool
    message: str

