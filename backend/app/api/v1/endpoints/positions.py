"""
Position management endpoints.
Complete implementation with PositionService.
"""

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_position_service
from app.domain.position.exceptions import PositionNotFoundError
from app.domain.position.schemas import (
    PositionCreate,
    PositionEntry,
    PositionResponse,
    PositionWithPnL,
    TpSlEvaluationRequest,
    TpSlEvaluationResponse,
)
from app.domain.position.service import PositionService

router = APIRouter(prefix="/positions", tags=["positions"])


@router.get("/", response_model=list[PositionResponse])
async def list_positions(
    service: PositionService = Depends(get_position_service)
):
    """
    List open positions for the user.

    Args:
        service: Position service dependency

    Returns:
        List of open position responses
    """
    return await service.get_open_positions()


@router.post("/", response_model=PositionResponse, status_code=201)
async def create_position(
    data: PositionCreate,
    service: PositionService = Depends(get_position_service)
):
    """
    Create new position with calculated avg_price.

    Args:
        data: Position creation data
        service: Position service dependency

    Returns:
        Created position response
    """
    return await service.create_position(data)


@router.get(
    "/{position_id}",
    response_model=PositionResponse
)
async def get_position(
    position_id: UUID,
    service: PositionService = Depends(get_position_service)
):
    """
    Get single position by ID.

    Args:
        position_id: Position unique identifier
        service: Position service dependency

    Returns:
        Position response

    Raises:
        HTTPException: 404 if position not found
    """
    position = await service._repository.get_by_id(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.patch(
    "/{position_id}/entries",
    response_model=PositionResponse
)
async def add_entry(
    position_id: UUID,
    entry: PositionEntry,
    service: PositionService = Depends(get_position_service)
):
    """
    Add new entry to existing position.

    Args:
        position_id: Position unique identifier
        entry: New position entry to add
        service: Position service dependency

    Returns:
        Updated position response with recalculated avg_price

    Raises:
        HTTPException: 404 if position not found
    """
    result = await service.add_entry(position_id, entry)
    if not result:
        raise HTTPException(status_code=404, detail="Position not found")
    return result


@router.delete("/{position_id}", status_code=204)
async def close_position(
    position_id: UUID,
    service: PositionService = Depends(get_position_service)
):
    """
    Close position (soft delete).

    Args:
        position_id: Position unique identifier
        service: Position service dependency

    Raises:
        HTTPException: 404 if position not found
    """
    success = await service.close_position(position_id)
    if not success:
        raise HTTPException(status_code=404, detail="Position not found")


@router.get("/{position_id}/pnl", response_model=PositionWithPnL)
async def get_position_pnl(
    position_id: UUID,
    current_price: Decimal = Query(
        description="Current market price for P&L calculation",
        gt=0,
        examples=[Decimal("150.25")]
    ),
    service: PositionService = Depends(get_position_service)
):
    """
    Get position with calculated P&L data.

    Args:
        position_id: Position unique identifier
        current_price: Current market price for P&L calculation
        service: Position service dependency

    Returns:
        Position enriched with P&L calculations

    Raises:
        HTTPException: 404 if position not found
        HTTPException: 422 if current_price is invalid
    """
    try:
        return await service.get_position_with_pnl(position_id, current_price)
    except PositionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{position_id}/evaluate",
    response_model=TpSlEvaluationResponse
)
async def evaluate_tp_sl(
    position_id: UUID,
    request: TpSlEvaluationRequest,
    service: PositionService = Depends(get_position_service)
):
    """
    Evaluate TP/SL levels against current price.
    Returns action recommendation: hold/partial_sell/full_exit
    """
    try:
        return await service.evaluate_tp_sl(
            position_id=position_id,
            current_price=request.current_price,
            take_profit_levels=request.take_profit_levels,
            stop_loss_levels=request.stop_loss_levels,
        )
    except PositionNotFoundError:
        raise HTTPException(status_code=404, detail="Position not found")
