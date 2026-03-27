"""
API v1 router aggregating all v1 endpoints.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, positions

api_router = APIRouter()

# Include all v1 endpoint routers
api_router.include_router(health.router, prefix="")
api_router.include_router(positions.router, prefix="")
