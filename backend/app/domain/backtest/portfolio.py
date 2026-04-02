"""
Virtual portfolio for backtest simulation.
Pure stateful class — no I/O, no async.
Tracks cash + positions + trade history.
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from app.domain.backtest.exceptions import (
    InsufficientCapitalError,
    InsufficientPositionError,
)
from app.domain.backtest.schemas import BacktestTrade

PRECISION = Decimal("0.0001")


class VirtualPortfolio:
    """
    Virtual portfolio for backtest simulation.
    Pure stateful class — no I/O, no async.
    Tracks cash + positions + trade history.
    """

    def __init__(self, initial_capital: Decimal):
        self._initial_capital = initial_capital
        self._cash = initial_capital
        self._positions: dict[str, dict] = {}
        # {ticker: {quantity, avg_price, cost_basis}}
        self._trades: list[BacktestTrade] = []
        self._realized_pnl = Decimal("0")

    def buy(
        self,
        ticker: str,
        quantity: Decimal,
        price: Decimal,
        trade_date: date,
        trigger: str = "signal",
    ) -> BacktestTrade:
        """
        Execute buy order.
        Raises InsufficientCapitalError if not enough cash.
        Updates position with weighted avg_price.
        """
        cost = (quantity * price).quantize(PRECISION)
        if cost > self._cash:
            raise InsufficientCapitalError(cost, self._cash)

        self._cash -= cost

        if ticker in self._positions:
            pos = self._positions[ticker]
            existing_cost = pos["avg_price"] * pos["quantity"]
            new_total_qty = pos["quantity"] + quantity
            new_avg = ((existing_cost + cost) / new_total_qty).quantize(PRECISION)
            self._positions[ticker] = {
                "quantity": new_total_qty,
                "avg_price": new_avg,
                "cost_basis": (existing_cost + cost).quantize(PRECISION),
            }
        else:
            self._positions[ticker] = {
                "quantity": quantity,
                "avg_price": price.quantize(PRECISION),
                "cost_basis": cost,
            }

        trade = BacktestTrade(
            date=trade_date,
            ticker=ticker,
            action="buy",
            quantity=quantity,
            price=price,
            pnl=Decimal("0"),
            trigger=trigger,
            holding_days=0,
        )
        self._trades.append(trade)
        return trade

    def sell(
        self,
        ticker: str,
        quantity: Decimal,
        price: Decimal,
        trade_date: date,
        trigger: str = "signal",
        holding_days: int = 0,
    ) -> BacktestTrade:
        """
        Execute sell order.
        Raises InsufficientPositionError if not enough shares.
        """
        if ticker not in self._positions:
            raise InsufficientPositionError(ticker, quantity, Decimal("0"))

        pos = self._positions[ticker]
        if quantity > pos["quantity"]:
            raise InsufficientPositionError(ticker, quantity, pos["quantity"])

        proceeds = (quantity * price).quantize(PRECISION)
        pnl = ((price - pos["avg_price"]) * quantity).quantize(PRECISION)

        self._cash += proceeds
        self._realized_pnl += pnl

        remaining = pos["quantity"] - quantity
        if remaining <= 0:
            del self._positions[ticker]
        else:
            self._positions[ticker]["quantity"] = remaining
            # Update cost basis proportionally
            ratio = remaining / pos["quantity"]
            self._positions[ticker]["cost_basis"] = (
                pos["cost_basis"] * ratio
            ).quantize(PRECISION)

        trade = BacktestTrade(
            date=trade_date,
            ticker=ticker,
            action="sell",
            quantity=quantity,
            price=price,
            pnl=pnl,
            trigger=trigger,
            holding_days=holding_days,
        )
        self._trades.append(trade)
        return trade

    def total_value(self, current_prices: dict[str, Decimal]) -> Decimal:
        """Calculate total portfolio value."""
        position_value = sum(
            pos["quantity"] * current_prices.get(ticker, pos["avg_price"])
            for ticker, pos in self._positions.items()
        )
        return (self._cash + position_value).quantize(PRECISION)

    @property
    def cash(self) -> Decimal:
        return self._cash

    @property
    def positions(self) -> dict:
        return dict(self._positions)

    @property
    def trades(self) -> list[BacktestTrade]:
        return list(self._trades)

    @property
    def realized_pnl(self) -> Decimal:
        return self._realized_pnl