"""
Scheduler API endpoints.
Provides scheduler status, monitoring, and recovery operations.
"""

from datetime import date
from typing import Any

from fastapi import APIRouter, Query

from app.core.config import get_settings
from app.core.container import get_container
from app.infra.db.base import AsyncSessionLocal
from app.scheduler.recovery import RecoveryManager
from app.scheduler.scheduler import get_scheduler_manager

router = APIRouter()


@router.get("/status")
async def get_scheduler_status() -> dict[str, Any]:
    """Get current scheduler status and next job run times."""
    settings = get_settings()
    scheduler_manager = get_scheduler_manager()
    scheduler_status = scheduler_manager.get_job_status()

    # Add recovery configuration to status
    scheduler_status.update({
        "recovery_enabled": True,
        "max_recovery_days": settings.max_recovery_days,
        # TODO: Add last_recovery_check timestamp in future iteration
    })

    return scheduler_status


@router.post("/recover")
async def manual_recovery(
    market: str | None = Query(
        default=None,
        description="KR, US, or None for both"
    ),
) -> dict[str, Any]:
    """
    Manually trigger missed execution recovery check.
    Useful for testing and manual operation.
    """
    async with AsyncSessionLocal() as session:
        container = get_container()
        kr_repo = container.analysis_log_repository(session)
        us_repo = container.analysis_log_repository(session)
        recovery = RecoveryManager(kr_repo, us_repo)

        if market == "KR":
            today = date.today()
            result = await recovery._recover_market("KR", today, kr_repo)
            return {"kr": result}
        elif market == "US":
            today = date.today()
            result = await recovery._recover_market("US", today, us_repo)
            return {"us": result}
        else:
            # Both markets
            results = await recovery.check_and_recover()
            return results
