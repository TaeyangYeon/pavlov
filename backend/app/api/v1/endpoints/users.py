from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.container import get_container
from app.domain.user.exceptions import InvalidAPIKeyError, UserNotFoundError
from app.domain.user.schemas import (
    APIKeySetRequest,
    APIKeySetResponse,
    UserCreate,
    UserResponse,
)
from app.infra.db.base import get_async_session
from app.infra.db.models.user import User

router = APIRouter(prefix="/users", tags=["users"])

STUB_USER_ID = UUID(
    "00000000-0000-0000-0000-000000000001"
)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=201
)
async def create_user(
    data: UserCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """Create new user account."""
    service = get_container().user_service(session)
    return await service.create_user(data)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get current user profile.
    Uses stub user until auth implemented.
    """
    service = get_container().user_service(session)
    try:
        return await service.get_user(STUB_USER_ID)
    except UserNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )


@router.post(
    "/me/api-key",
    response_model=APIKeySetResponse
)
async def set_api_key(
    request: APIKeySetRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Set and validate Anthropic API key.
    Key is validated before encrypted storage.
    """
    service = get_container().user_service(session)
    try:
        return await service.set_api_key(
            STUB_USER_ID, request
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=404, detail="User not found"
        )
    except InvalidAPIKeyError as e:
        raise HTTPException(
            status_code=422, detail=str(e)
        )


@router.get("/me/api-key/status")
async def get_api_key_status(
    session: AsyncSession = Depends(get_async_session),
):
    """
    Check if API key is set (without revealing the key).
    """
    service = get_container().user_service(session)
    key = await service.get_api_key(STUB_USER_ID)
    return {
        "has_api_key": key is not None,
        "key_preview": (
            f"{key[:8]}..." if key else None
        )
    }


@router.delete("/me/api-key", status_code=204)
async def delete_api_key(
    session: AsyncSession = Depends(get_async_session),
):
    """Remove stored API key."""
    # Actually clear it by setting to None
    stmt = (
        update(User)
        .where(User.id == STUB_USER_ID)
        .values(api_key_encrypted=None)
    )
    await session.execute(stmt)
    await session.commit()
