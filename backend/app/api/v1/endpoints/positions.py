"""
Position management endpoints.
Stub implementation - real logic added in Step 11.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_position_repository
from app.domain.position.interfaces import PositionRepositoryPort
from app.domain.position.schemas import PositionCreate, PositionResponse

router = APIRouter(prefix="/positions", tags=["positions"])


@router.get("/", response_model=list[PositionResponse])
async def list_positions(
    repository: PositionRepositoryPort = Depends(get_position_repository),
):
    """
    List user positions.

    Args:
        repository: Position repository dependency

    Returns:
        List of position responses

    Raises:
        HTTPException: 501 Not Implemented (Step 11)
    """
    # TODO Step 11: wire real user_id from auth
    raise HTTPException(status_code=501, detail="Implement in Step 11")


@router.post("/", response_model=PositionResponse, status_code=201)
async def create_position(
    data: PositionCreate,
    repository: PositionRepositoryPort = Depends(get_position_repository),
):
    """
    Create new position.

    Args:
        data: Position creation data
        repository: Position repository dependency

    Returns:
        Created position response

    Raises:
        HTTPException: 501 Not Implemented (Step 11)
    """
    raise HTTPException(status_code=501, detail="Implement in Step 11")
