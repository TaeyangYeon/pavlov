"""
Health check endpoint for system monitoring.
"""

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("/health", tags=["system"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: System health status
    """
    return {"status": "ok", "version": "0.1.0", "environment": get_settings().APP_ENV}
