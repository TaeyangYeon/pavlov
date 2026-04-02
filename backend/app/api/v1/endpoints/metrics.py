"""
Metrics API endpoints for Step 26: Performance Optimization.
Provides real-time performance metrics and alerts.
"""

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.metrics import get_metrics_collector

router = APIRouter(
    prefix="/metrics", tags=["metrics"]
)


@router.get("/performance")
async def get_performance_metrics():
    """
    Get real-time performance metrics.
    Cache hit rates, AI costs, system stats.
    """
    collector = get_metrics_collector()
    summary = collector.get_summary()

    settings = get_settings()
    total_ai_cost = collector.get_total_ai_cost()
    cost_alert = (
        float(total_ai_cost)
        > settings.ai_cost_alert_threshold_usd
    )

    return {
        **summary,
        "alerts": {
            "ai_cost_exceeded": cost_alert,
            "ai_cost_threshold_usd": (
                settings.ai_cost_alert_threshold_usd
            ),
            "total_ai_cost_usd": float(total_ai_cost),
        },
        "targets": {
            "cache_hit_rate_target": 90.0,
            "ai_cost_per_run_target_usd": 0.10,
            "slow_query_threshold_ms": (
                settings.slow_query_threshold_ms
            ),
        }
    }


@router.post("/reset")
async def reset_metrics():
    """Reset in-memory metrics counters."""
    collector = get_metrics_collector()
    collector.reset()
    return {"message": "Metrics reset successfully"}