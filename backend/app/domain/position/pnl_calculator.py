"""
PnL Calculation Engine.
Pure deterministic calculations with Decimal precision.
"""

from decimal import Decimal

from app.domain.position.exceptions import InvalidPriceError
from app.domain.position.schemas import PnLResult, PositionResponse


class PnLCalculator:
    """
    Pure calculation engine for P&L computations.
    Single responsibility: deterministic financial calculations.
    No I/O operations, no external dependencies.
    """

    def calculate_unrealized(
        self, position: PositionResponse, current_price: Decimal
    ) -> PnLResult:
        """
        Calculate unrealized P&L for an open position.
        
        Formula:
        - Current Value = total_quantity * current_price
        - Cost Basis = total_quantity * avg_price  
        - Unrealized P&L = current_value - cost_basis
        - Unrealized P&L % = (current_price - avg_price) / avg_price * 100
        
        Args:
            position: Position with entries and avg_price
            current_price: Current market price per share
            
        Returns:
            PnLResult with unrealized P&L calculations
            
        Raises:
            InvalidPriceError: If current_price <= 0
        """
        if current_price <= 0:
            raise InvalidPriceError("Current price must be positive")

        # Calculate total quantity from entries
        total_quantity = sum(entry.quantity for entry in position.entries)

        # Handle edge cases
        if total_quantity == 0 or not position.avg_price or position.avg_price == 0:
            return PnLResult(
                unrealized_pnl=Decimal("0.0000"),
                unrealized_pnl_percent=Decimal("0.0000"),
                realized_pnl=Decimal("0.0000"),
                total_pnl=Decimal("0.0000")
            )

        # Calculate P&L
        current_value = total_quantity * current_price
        cost_basis = total_quantity * position.avg_price
        unrealized_pnl = current_value - cost_basis

        # Calculate percentage change
        unrealized_pnl_percent = (
            (current_price - position.avg_price) / position.avg_price * 100
        )

        # Quantize to 4 decimal places
        unrealized_pnl = unrealized_pnl.quantize(Decimal("0.0001"))
        unrealized_pnl_percent = unrealized_pnl_percent.quantize(Decimal("0.0001"))

        return PnLResult(
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_percent=unrealized_pnl_percent,
            realized_pnl=Decimal("0.0000"),
            total_pnl=unrealized_pnl
        )

    def calculate_realized(
        self,
        original_position: PositionResponse,
        remaining_position: PositionResponse | None,
        sale_price: Decimal
    ) -> PnLResult:
        """
        Calculate realized P&L from a position sale.
        
        Formula:
        - Quantity Sold = original_quantity - remaining_quantity
        - Realized P&L = quantity_sold * (sale_price - avg_price)
        
        Args:
            original_position: Position before sale
            remaining_position: Position after sale (None if fully sold)
            sale_price: Price per share at sale
            
        Returns:
            PnLResult with realized P&L calculations
            
        Raises:
            InvalidPriceError: If sale_price <= 0
        """
        if sale_price <= 0:
            raise InvalidPriceError("Sale price must be positive")

        # Calculate quantities
        original_quantity = sum(entry.quantity for entry in original_position.entries)
        remaining_quantity = Decimal("0")
        if remaining_position:
            remaining_quantity = sum(entry.quantity for entry in remaining_position.entries)

        quantity_sold = original_quantity - remaining_quantity

        # Handle edge cases
        if quantity_sold == 0 or not original_position.avg_price:
            return PnLResult(
                unrealized_pnl=Decimal("0.0000"),
                unrealized_pnl_percent=Decimal("0.0000"),
                realized_pnl=Decimal("0.0000"),
                total_pnl=Decimal("0.0000")
            )

        # Calculate realized P&L
        realized_pnl = quantity_sold * (sale_price - original_position.avg_price)
        realized_pnl = realized_pnl.quantize(Decimal("0.0001"))

        return PnLResult(
            unrealized_pnl=Decimal("0.0000"),
            unrealized_pnl_percent=Decimal("0.0000"),
            realized_pnl=realized_pnl,
            total_pnl=realized_pnl
        )
