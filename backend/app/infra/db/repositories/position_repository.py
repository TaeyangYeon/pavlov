"""
PositionRepository concrete implementation.
Implements PositionRepositoryPort interface with stub methods.
Real implementation will be added in Step 11.
"""

from uuid import UUID

from app.domain.position.interfaces import PositionRepositoryPort
from app.domain.position.schemas import PositionCreate, PositionResponse
from sqlalchemy.ext.asyncio import AsyncSession


class PositionRepository(PositionRepositoryPort):
    """
    Concrete implementation of PositionRepositoryPort.
    Currently contains stubs - real logic added in Step 11.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, data: PositionCreate, user_id: UUID) -> PositionResponse:
        """Create a new position."""
        # TODO Step 11: implement real DB insert
        raise NotImplementedError("Implement in Step 11")

    async def get_by_id(self, position_id: UUID) -> PositionResponse | None:
        """Get position by ID."""
        # TODO Step 11: implement real DB query
        raise NotImplementedError("Implement in Step 11")

    async def get_by_user(self, user_id: UUID) -> list[PositionResponse]:
        """Get all positions for a user."""
        # TODO Step 11: implement real DB query
        raise NotImplementedError("Implement in Step 11")

    async def get_open_positions(self, user_id: UUID) -> list[PositionResponse]:
        """Get only open positions for a user."""
        # TODO Step 11: implement real DB query
        raise NotImplementedError("Implement in Step 11")

    async def update(self, position_id: UUID, data: dict) -> PositionResponse | None:
        """Update position data."""
        # TODO Step 11: implement real DB update
        raise NotImplementedError("Implement in Step 11")

    async def delete(self, position_id: UUID) -> bool:
        """Delete a position."""
        # TODO Step 11: implement real DB delete
        raise NotImplementedError("Implement in Step 11")
