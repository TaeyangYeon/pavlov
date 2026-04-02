"""
Backtests a strategy against historical OHLCV data.

Pipeline:
Day N: calculate indicators → apply filters
       → evaluate TP/SL on existing positions
       → generate signals
Day N+1: execute trades at open price (no lookahead)
"""

from datetime import date
from decimal import Decimal

from app.domain.ai.schemas import StopLossLevel, TakeProfitLevel
from app.domain.backtest.exceptions import InsufficientHistoryError, InsufficientCapitalError, InsufficientPositionError
from app.domain.backtest.metrics import PerformanceMetrics
from app.domain.backtest.portfolio import VirtualPortfolio
from app.domain.backtest.schemas import BacktestRunResult, DailyValue
from app.domain.position.pnl_calculator import PnLCalculator
from app.domain.position.tp_sl_engine import TpSlEngine

MIN_HISTORY_DAYS = 60  # for MA60 calculation


class BacktestSimulator:
    """
    Backtests a strategy against historical OHLCV data.

    Pipeline:
    Day N: calculate indicators → apply filters
           → evaluate TP/SL on existing positions
           → generate signals
    Day N+1: execute trades at open price (no lookahead)
    """

    def __init__(self):
        self._tp_sl_engine = TpSlEngine()
        self._pnl_calc = PnLCalculator()
        self._metrics_calc = PerformanceMetrics()

    def run(
        self,
        ticker: str,
        market: str,
        ohlcv_data: list[dict],
        initial_capital: Decimal,
        quantity_per_trade: Decimal,
        take_profit_levels: list[TakeProfitLevel],
        stop_loss_levels: list[StopLossLevel],
    ) -> BacktestRunResult:
        """
        Run backtest simulation.
        ohlcv_data: sorted OLDEST first, NEWEST last.
        Returns BacktestRunResult with full trade history.
        """
        if len(ohlcv_data) < MIN_HISTORY_DAYS:
            raise InsufficientHistoryError(ticker, MIN_HISTORY_DAYS, len(ohlcv_data))

        portfolio = VirtualPortfolio(initial_capital)
        daily_values: list[DailyValue] = []

        # Track buy date for holding_days calculation
        buy_date: date | None = None
        pending_action: str | None = None

        for i, day in enumerate(ohlcv_data):
            day_date = self._parse_date(day["date"])
            close = Decimal(str(day["close"]))
            open_price = Decimal(str(day["open"]))

            # Execute pending action from previous day signal
            if pending_action and i > 0:  # Don't execute on first day
                if pending_action == "sell":
                    holding = (day_date - buy_date).days if buy_date else 0
                    ticker_pos = portfolio.positions.get(ticker)
                    if ticker_pos:
                        qty = ticker_pos["quantity"]
                        try:
                            portfolio.sell(
                                ticker=ticker,
                                quantity=qty,
                                price=open_price,
                                trade_date=day_date,
                                trigger="tp_sl",
                                holding_days=holding,
                            )
                            buy_date = None
                        except InsufficientPositionError:
                            pass
                elif pending_action == "buy":
                    if ticker not in portfolio.positions:
                        try:
                            portfolio.buy(
                                ticker=ticker,
                                quantity=quantity_per_trade,
                                price=open_price,
                                trade_date=day_date,
                            )
                            buy_date = day_date
                        except InsufficientCapitalError:
                            pass

            pending_action = None

            # Evaluate current position against TP/SL
            pos = portfolio.positions.get(ticker)
            if pos:
                avg_price = pos["avg_price"]
                qty = pos["quantity"]
                decision = self._tp_sl_engine.evaluate(
                    avg_price=avg_price,
                    current_price=close,
                    total_quantity=qty,
                    take_profit_levels=take_profit_levels,
                    stop_loss_levels=stop_loss_levels,
                )
                if decision.action != "hold":
                    pending_action = "sell"
            else:
                # No position — consider buying
                # Simple signal: if no position, always buy (except last day)
                if i < len(ohlcv_data) - 1:
                    pending_action = "buy"

            # Record daily portfolio value
            current_value = portfolio.total_value({ticker: close})
            prev_value = (
                daily_values[-1].portfolio_value
                if daily_values
                else initial_capital
            )
            daily_return = (
                (current_value - prev_value) / prev_value * Decimal("100")
            ).quantize(Decimal("0.0001"))

            daily_values.append(
                DailyValue(
                    date=day_date,
                    portfolio_value=current_value,
                    cash=portfolio.cash,
                    position_value=(current_value - portfolio.cash),
                    daily_return_pct=daily_return,
                )
            )

        # Close any remaining position at last price
        last_day = ohlcv_data[-1]
        last_close = Decimal(str(last_day["close"]))
        last_date = self._parse_date(last_day["date"])
        pos = portfolio.positions.get(ticker)
        if pos and buy_date:
            holding = (last_date - buy_date).days
            try:
                portfolio.sell(
                    ticker=ticker,
                    quantity=pos["quantity"],
                    price=last_close,
                    trade_date=last_date,
                    trigger="eod",
                    holding_days=holding,
                )
            except Exception:
                pass

        final_value = portfolio.total_value({ticker: last_close})
        metrics = self._metrics_calc.calculate(
            initial_capital=initial_capital,
            daily_values=daily_values,
            trades=portfolio.trades,
        )

        start_date = self._parse_date(ohlcv_data[0]["date"])
        end_date = last_date

        return BacktestRunResult(
            ticker=ticker,
            market=market,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_capital=final_value,
            metrics=metrics,
            trades=portfolio.trades,
            daily_values=daily_values,
        )

    def _parse_date(self, date_str: str | date) -> date:
        if isinstance(date_str, date):
            return date_str
        return date.fromisoformat(str(date_str)[:10])