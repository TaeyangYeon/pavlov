"""
PositionService for position business logic.
Orchestrates position operations with avg_price calculation.
"""

from decimal import Decimal
from uuid import UUID

from app.domain.ai.schemas import StopLossLevel, TakeProfitLevel
from app.domain.position.exceptions import PositionNotFoundError
from app.domain.position.interfaces import PositionRepositoryPort
from app.domain.position.pnl_calculator import PnLCalculator
from app.domain.position.schemas import (
    PositionCreate,
    PositionEntry,
    PositionResponse,
    PositionWithPnL,
    TpSlEvaluationResponse,
    TrailingStopConfig,
    TrailingStopEvaluationResponse,
)
from app.domain.position.tp_sl_engine import TpSlEngine
from app.domain.position.trailing_stop_engine import TrailingStopEngine

# TODO: replace with real auth in future step
STUB_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


class PositionService:
    """
    Orchestrates position business logic.
    Single responsibility: avg_price calculation + delegation.
    """

    def __init__(
        self,
        repository: PositionRepositoryPort,
        calculator: PnLCalculator | None = None,
        tp_sl_engine: TpSlEngine | None = None,
        trailing_stop_engine: TrailingStopEngine | None = None,
    ):
        self._repository = repository
        self._calculator = calculator or PnLCalculator()
        self._tp_sl_engine = tp_sl_engine or TpSlEngine()
        self._trailing_stop_engine = (
            trailing_stop_engine or TrailingStopEngine()
        )

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

        pnl_result = self._calculator.calculate_unrealized(position, current_price)

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
            pnl_result = self._calculator.calculate_unrealized(position, current_price)

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

    async def evaluate_tp_sl(
        self,
        position_id: UUID,
        current_price: Decimal,
        take_profit_levels: list[TakeProfitLevel],
        stop_loss_levels: list[StopLossLevel],
    ) -> TpSlEvaluationResponse:
        """
        Evaluate TP/SL for a position at current price.
        Raises PositionNotFoundError if position not found.
        """
        position = await self._repository.get_by_id(position_id)
        if not position:
            raise PositionNotFoundError(f"Position {position_id} not found")

        total_quantity = sum(
            e.quantity for e in position.entries
        )

        decision = self._tp_sl_engine.evaluate(
            avg_price=position.avg_price,
            current_price=current_price,
            total_quantity=total_quantity,
            take_profit_levels=take_profit_levels,
            stop_loss_levels=stop_loss_levels,
        )

        return TpSlEvaluationResponse(
            position_id=position_id,
            ticker=position.ticker,
            action=decision.action,
            triggered_by=decision.triggered_by,
            triggered_level_pct=decision.triggered_level_pct,
            sell_quantity=decision.sell_quantity,
            sell_ratio=decision.sell_ratio,
            current_pnl_pct=decision.current_pnl_pct,
            realized_pnl_estimate=decision.realized_pnl_estimate,
            avg_price=position.avg_price,
            current_price=current_price,
            total_quantity=total_quantity,
        )

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

    async def evaluate_trailing_stop(
        self,
        position_id: UUID,
        current_price: Decimal,
        config: TrailingStopConfig,
    ) -> TrailingStopEvaluationResponse:
        """
        Evaluate trailing stop and update HWM in DB.
        Raises PositionNotFoundError if position not found.
        """
        position = await self._repository.get_by_id(position_id)
        if not position:
            raise PositionNotFoundError(position_id)

        result = self._trailing_stop_engine.evaluate(
            current_price=current_price,
            high_water_mark=position.high_water_mark,
            avg_price=position.avg_price,
            config=config,
        )

        # Persist updated HWM to DB
        hwm_updated = result.high_water_mark != (
            position.high_water_mark or Decimal("0")
        )
        if hwm_updated:
            await self._repository.update(
                position_id,
                {"high_water_mark": result.high_water_mark}
            )

        return TrailingStopEvaluationResponse(
            position_id=position_id,
            ticker=position.ticker,
            triggered=result.triggered,
            action=result.action,
            high_water_mark=result.high_water_mark,
            stop_price=result.stop_price,
            current_price=current_price,
            trail_distance_pct=result.trail_distance_pct,
            distance_to_stop_pct=result.distance_to_stop_pct,
            new_high_water_mark=result.high_water_mark,
            hwm_updated=hwm_updated,
        )

    async def evaluate_full_position(
        self,
        position_id: UUID,
        current_price: Decimal,
        take_profit_levels: list[TakeProfitLevel],
        stop_loss_levels: list[StopLossLevel],
        trailing_config: TrailingStopConfig | None = None,
    ) -> dict:
        """
        Combined evaluation: TP/SL + Trailing Stop.
        Priority: SL → TP → Trailing Stop
        Returns unified action recommendation.
        """
        # Step 1: TP/SL evaluation
        tp_sl = await self.evaluate_tp_sl(
            position_id, current_price,
            take_profit_levels, stop_loss_levels
        )

        # If TP/SL triggered, no need for trailing stop
        if tp_sl.action != "hold":
            return {
                "action": tp_sl.action,
                "source": "tp_sl",
                "tp_sl_result": tp_sl,
                "trailing_result": None,
            }

        # Step 2: Trailing stop (only if TP/SL says hold)
        if trailing_config:
            trailing = await self.evaluate_trailing_stop(
                position_id, current_price, trailing_config
            )
            if trailing.triggered:
                return {
                    "action": "full_exit",
                    "source": "trailing_stop",
                    "tp_sl_result": tp_sl,
                    "trailing_result": trailing,
                }

        return {
            "action": "hold",
            "source": "none",
            "tp_sl_result": tp_sl,
            "trailing_result": None,
        }
