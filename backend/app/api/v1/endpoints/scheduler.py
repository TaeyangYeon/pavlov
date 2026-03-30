"""
Scheduler API endpoints.
Provides scheduler status and monitoring.
"""

from fastapi import APIRouter
from app.scheduler.scheduler import get_scheduler_manager

router = APIRouter()


@router.get("/status")
async def get_scheduler_status():
    """Get current scheduler status and next job run times."""
    scheduler_manager = get_scheduler_manager()
    return scheduler_manager.get_job_status()