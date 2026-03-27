"""
CORS middleware configuration.
"""

from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings


def setup_cors_middleware(app):
    """
    Setup CORS middleware for the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    settings = get_settings()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
