"""
PositionRepository concrete implementation.
Implements PositionRepositoryPort interface with real SQLAlchemy operations.
"""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.position.interfaces import PositionRepositoryPort
from app.domain.position.schemas import PositionCreate, PositionEntry, PositionResponse
from app.infra.db.models.position import Position


class PositionRepository(PositionRepositoryPort):
    """
    Concrete implementation of PositionRepositoryPort.
    Uses SQLAlchemy 2.0 async syntax for database operations.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, data: PositionCreate, user_id: UUID) -> PositionResponse:
        """Create a new position."""
        position = Position(
            user_id=user_id,
            ticker=data.ticker,
            market=data.market,
            entries=[
                {
                    "price": float(e.price),
                    "quantity": float(e.quantity),
                    "entered_at": e.entered_at.isoformat()
                }
                for e in data.entries
            ],
            avg_price=data.avg_price,  # pre-calculated by service
            status="open"
        )
        self._session.add(position)
        await self._session.commit()
        await self._session.refresh(position)
        return self._to_response(position)

    async def get_by_id(self, position_id: UUID) -> PositionResponse | None:
        """Get position by ID."""
        stmt = select(Position).where(
            Position.id == position_id
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_response(row) if row else None

    async def get_by_user(self, user_id: UUID) -> list[PositionResponse]:
        """Get all positions for a user."""
        stmt = select(Position).where(
            Position.user_id == user_id
        ).order_by(Position.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_response(r) for r in result.scalars()]

    async def get_open_positions(self, user_id: UUID) -> list[PositionResponse]:
        """Get only open positions for a user."""
        stmt = select(Position).where(
            Position.user_id == user_id,
            Position.status == "open"
        ).order_by(Position.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_response(r) for r in result.scalars()]

    async def update(self, position_id: UUID, data: dict) -> PositionResponse | None:
        """Update position data."""
        stmt = (
            update(Position)
            .where(Position.id == position_id)
            .values(**data)
            .returning(Position)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        row = result.scalar_one_or_none()
        return self._to_response(row) if row else None

    async def delete(self, position_id: UUID) -> bool:
        """Soft delete: set status to closed."""
        stmt = (
            update(Position)
            .where(Position.id == position_id)
            .values(status="closed")
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount > 0

    def _to_response(self, row: Position) -> PositionResponse:
        """Convert Position model to PositionResponse schema."""
        return PositionResponse(
            id=row.id,
            ticker=row.ticker,
            market=str(row.market.value
                       if hasattr(row.market, 'value')
                       else row.market),
            entries=[
                PositionEntry(**e) for e in row.entries
            ],
            avg_price=row.avg_price,
            status=str(row.status.value
                       if hasattr(row.status, 'value')
                       else row.status),
            created_at=row.created_at,
            updated_at=row.updated_at
        )
