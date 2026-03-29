"""
PositionService for position business logic.
Orchestrates position operations with avg_price calculation.
"""

from decimal import Decimal
from uuid import UUID

from app.domain.position.exceptions import PositionNotFoundError
from app.domain.position.interfaces import PositionRepositoryPort
from app.domain.position.pnl_calculator import PnLCalculator
from app.domain.position.schemas import (
    PositionCreate,
    PositionEntry,
    PositionResponse,
    PositionWithPnL,
)

# TODO: replace with real auth in future step
STUB_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


class PositionService:
    """
    Orchestrates position business logic.
    Single responsibility: avg_price calculation + delegation.
    """

    def __init__(self, repository: PositionRepositoryPort):
        self._repository = repository
        self._pnl_calculator = PnLCalculator()

    async def create_position(self, data: PositionCreate) -> PositionResponse:
        """Create a new position with calculated avg_price."""
        avg_price = self._calculate_avg_price(data.entries)
        data_with_avg = data.model_copy(
            update={"avg_price": avg_price}
        )
        return await self._repository.create(
            data_with_avg, STUB_USER_ID
        )

    async def add_entry(
        self,
        position_id: UUID,
        new_entry: PositionEntry
    ) -> PositionResponse | None:
        """Add new entry to existing position and recalculate avg_price."""
        existing = await self._repository.get_by_id(position_id)
        if not existing:
            return None

        updated_entries = existing.entries + [new_entry]
        new_avg = self._calculate_avg_price(updated_entries)
        return await self._repository.update(
            position_id,
            {
                "entries": [
                    {
                        "price": float(e.price),
                        "quantity": float(e.quantity),
                        "entered_at": e.entered_at.isoformat()
                    }
                    for e in updated_entries
                ],
                "avg_price": new_avg
            }
        )

    async def get_open_positions(self) -> list[PositionResponse]:
        """Get all open positions for the stub user."""
        return await self._repository.get_open_positions(
            STUB_USER_ID
        )

    async def close_position(self, position_id: UUID) -> bool:
        """Close a position (soft delete)."""
        return await self._repository.delete(position_id)

    async def get_position_with_pnl(
        self, position_id: UUID, current_price: Decimal
    ) -> PositionWithPnL:
        """Get a position enriched with P&L calculations."""
        position = await self._repository.get_by_id(position_id)
        if not position:
            raise PositionNotFoundError(f"Position {position_id} not found")

        pnl_result = self._pnl_calculator.calculate_unrealized(position, current_price)

        return PositionWithPnL(
            id=position.id,
            ticker=position.ticker,
            market=position.market,
            entries=position.entries,
            avg_price=position.avg_price,
            status=position.status,
            created_at=position.created_at,
            updated_at=position.updated_at,
            current_price=current_price,
            unrealized_pnl=pnl_result.unrealized_pnl,
            unrealized_pnl_percent=pnl_result.unrealized_pnl_percent,
            realized_pnl=pnl_result.realized_pnl,
            total_pnl=pnl_result.total_pnl,
        )

    async def get_all_positions_with_pnl(
        self, current_price: Decimal
    ) -> list[PositionWithPnL]:
        """Get all open positions enriched with P&L calculations."""
        positions = await self._repository.get_open_positions(STUB_USER_ID)

        positions_with_pnl = []
        for position in positions:
            pnl_result = self._pnl_calculator.calculate_unrealized(position, current_price)

            position_with_pnl = PositionWithPnL(
                id=position.id,
                ticker=position.ticker,
                market=position.market,
                entries=position.entries,
                avg_price=position.avg_price,
                status=position.status,
                created_at=position.created_at,
                updated_at=position.updated_at,
                current_price=current_price,
                unrealized_pnl=pnl_result.unrealized_pnl,
                unrealized_pnl_percent=pnl_result.unrealized_pnl_percent,
                realized_pnl=pnl_result.realized_pnl,
                total_pnl=pnl_result.total_pnl,
            )
            positions_with_pnl.append(position_with_pnl)

        return positions_with_pnl

    def _calculate_avg_price(
        self, entries: list[PositionEntry]
    ) -> Decimal:
        """
        Weighted average price calculation.
        avg = sum(price * quantity) / sum(quantity)
        """
        if not entries:
            return Decimal("0")

        total_value = sum(
            e.price * e.quantity for e in entries
        )
        total_qty = sum(e.quantity for e in entries)

        if total_qty == 0:
            return Decimal("0")

        return (total_value / total_qty).quantize(
            Decimal("0.0001")
        )
