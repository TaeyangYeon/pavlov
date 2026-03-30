"""
Strategy Integration endpoints.
Executes strategy analysis and returns unified strategy decisions.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.core.dependencies import get_strategy_integration_engine
from app.domain.ai.schemas import AIPromptOutput
from app.domain.position.schemas import TrailingStopConfig
from app.domain.strategy.engine import StrategyIntegrationEngine
from app.domain.strategy.schemas import StrategyRunResult

router = APIRouter(prefix="/strategy", tags=["strategy"])


@router.post("/run", response_model=StrategyRunResult)
async def run_strategy_analysis(
    market: str = Query(
        description="Market to analyze (KR or US)",
        regex="^(KR|US)$"
    ),
    run_date: date = Query(
        description="Analysis date",
        default_factory=date.today
    ),
    ai_output: AIPromptOutput | None = Body(
        default=None,
        description="AI analysis output from AnalysisPipeline"
    ),
    analysis_log_id: UUID | None = Body(
        default=None,
        description="Analysis log ID for DB linkage"
    ),
    trailing_configs: dict[str, TrailingStopConfig] | None = Body(
        default=None,
        description="Per-ticker trailing stop configurations"
    ),
    engine: StrategyIntegrationEngine = Depends(get_strategy_integration_engine),
):
    """
    Run full strategy integration for a market.
    
    Merges AI strategies with position engine results (TP/SL and trailing stop).
    Uses action severity hierarchy: hold < buy < partial_sell < full_exit.
    Only saves strategies that have changed from last run.
    
    Args:
        market: Market identifier ("KR" or "US")
        run_date: Analysis date
        ai_output: AI analysis output from AnalysisPipeline (optional)
        analysis_log_id: Analysis log ID for DB linkage (optional)
        trailing_configs: Per-ticker trailing stop configurations (optional)
        engine: Strategy integration engine dependency
        
    Returns:
        Complete strategy run result with unified strategies
        
    Raises:
        HTTPException: 422 if invalid market or data
        HTTPException: 500 if strategy execution fails
    """
    try:
        return await engine.run(
            market=market,
            run_date=run_date,
            ai_output=ai_output,
            analysis_log_id=analysis_log_id,
            trailing_configs=trailing_configs or {},
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Strategy execution failed: {str(e)}"
        )


@router.get("/health")
async def strategy_health():
    """
    Health check for strategy components.
    
    Returns:
        Status message indicating strategy system health
    """
    return {"status": "ok", "message": "Strategy Integration Engine ready"}