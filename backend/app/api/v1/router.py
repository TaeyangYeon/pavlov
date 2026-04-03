"""
API v1 router aggregating all v1 endpoints.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, positions, strategy, scheduler, users, decisions, behavior, backtest, metrics, notifications

api_router = APIRouter()

# Include all v1 endpoint routers
api_router.include_router(health.router, prefix="")
api_router.include_router(positions.router, prefix="")
api_router.include_router(strategy.router, prefix="")
api_router.include_router(scheduler.router, prefix="/scheduler")
api_router.include_router(users.router, prefix="")
api_router.include_router(decisions.router, prefix="")
api_router.include_router(behavior.router, prefix="")
api_router.include_router(backtest.router, prefix="")
api_router.include_router(metrics.router, prefix="")
api_router.include_router(notifications.router, prefix="")
