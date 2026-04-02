"""
Backtest API endpoints for strategy validation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.domain.ai.schemas import StopLossLevel, TakeProfitLevel
from app.domain.backtest.exceptions import InsufficientHistoryError
from app.domain.backtest.schemas import BacktestRequest, BacktestResponse, BACKTEST_DISCLAIMER
from app.domain.backtest.simulator import BacktestSimulator
from app.infra.db.models.market_data import MarketData
from app.infra.db.repositories.backtest_repository import BacktestRepository

router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest,
    save_result: bool = Query(default=True),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Run backtest simulation for a ticker.
    Fetches historical data from DB cache.
    Returns performance metrics + trade history.

    ⚠️ 과거 성과는 미래 수익을 보장하지 않습니다.
    """
    # Fetch historical data from DB
    stmt = (
        select(MarketData)
        .where(
            MarketData.ticker == request.ticker,
            MarketData.market == request.market,
            MarketData.date >= request.start_date,
            MarketData.date <= request.end_date,
        )
        .order_by(MarketData.date.asc())
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()

    if len(rows) < 60:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INSUFFICIENT_HISTORY",
                "message": (
                    f"Need at least 60 days of data, "
                    f"found {len(rows)}. "
                    f"Run the market data fetcher first."
                ),
            },
        )

    ohlcv_data = [
        {
            "ticker": r.ticker,
            "market": str(r.market.value if hasattr(r.market, "value") else r.market),
            "date": r.date.isoformat(),
            "open": float(r.open),
            "high": float(r.high),
            "low": float(r.low),
            "close": float(r.close),
            "volume": int(r.volume),
        }
        for r in rows
    ]

    # Build TP/SL levels
    tp_levels = [TakeProfitLevel(**lvl) for lvl in request.take_profit_levels]
    sl_levels = [StopLossLevel(**lvl) for lvl in request.stop_loss_levels]

    # Run simulation
    simulator = BacktestSimulator()
    try:
        run_result = simulator.run(
            ticker=request.ticker,
            market=request.market,
            ohlcv_data=ohlcv_data,
            initial_capital=request.initial_capital,
            quantity_per_trade=request.quantity_per_trade,
            take_profit_levels=tp_levels,
            stop_loss_levels=sl_levels,
        )
    except InsufficientHistoryError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Save result
    backtest_id = None
    if save_result:
        repo = BacktestRepository(session)
        saved = await repo.save(
            run_result,
            parameters=request.model_dump(mode="json"),
        )
        backtest_id = saved.id

    m = run_result.metrics

    return BacktestResponse(
        id=backtest_id,
        ticker=run_result.ticker,
        market=run_result.market,
        start_date=run_result.start_date,
        end_date=run_result.end_date,
        initial_capital=str(run_result.initial_capital),
        final_capital=str(run_result.final_capital),
        total_return_pct=str(m.total_return_pct),
        max_drawdown_pct=str(m.max_drawdown_pct),
        win_rate=str(m.win_rate),
        win_rate_pct=f"{float(m.win_rate)*100:.1f}%",
        sharpe_ratio=str(m.sharpe_ratio) if m.sharpe_ratio else None,
        total_trades=m.total_trades,
        winning_trades=m.winning_trades,
        losing_trades=m.losing_trades,
        best_day_pct=str(m.best_day_pct),
        worst_day_pct=str(m.worst_day_pct),
        avg_holding_days=str(m.avg_holding_days),
        trades=[
            {
                "date": t.date.isoformat(),
                "action": t.action,
                "quantity": str(t.quantity),
                "price": str(t.price),
                "pnl": str(t.pnl),
                "trigger": t.trigger,
                "holding_days": t.holding_days,
            }
            for t in run_result.trades
        ],
        daily_values=[
            {
                "date": dv.date.isoformat(),
                "portfolio_value": str(dv.portfolio_value),
                "daily_return_pct": str(dv.daily_return_pct),
            }
            for dv in run_result.daily_values
        ],
        disclaimer=run_result.disclaimer,
    )


@router.get("/history/{ticker}", response_model=list[BacktestResponse])
async def get_backtest_history(
    ticker: str,
    limit: int = Query(default=5, le=20),
    session: AsyncSession = Depends(get_db_session),
):
    """Get past backtest results for a ticker."""
    repo = BacktestRepository(session)
    rows = await repo.get_by_ticker(ticker, limit=limit)
    return [
        BacktestResponse(
            id=r.id,
            ticker=r.ticker,
            market=r.market,
            start_date=r.start_date,
            end_date=r.end_date,
            initial_capital=str(r.initial_capital),
            final_capital=str(r.final_capital),
            total_return_pct=str(r.total_return_pct),
            max_drawdown_pct=str(r.max_drawdown_pct),
            win_rate=str(r.win_rate),
            win_rate_pct=f"{float(r.win_rate)*100:.1f}%",
            sharpe_ratio=str(r.sharpe_ratio) if r.sharpe_ratio else None,
            total_trades=r.total_trades,
            winning_trades=0,  # Not stored separately in DB
            losing_trades=0,   # Not stored separately in DB
            best_day_pct="0",  # Not stored separately in DB
            worst_day_pct="0", # Not stored separately in DB
            avg_holding_days="0", # Not stored separately in DB
            trades=[],
            daily_values=[],
            disclaimer=BACKTEST_DISCLAIMER,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]