from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.middleware.cors import setup_cors_middleware
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.scheduler.scheduler import get_scheduler_manager

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan manager for scheduler startup/shutdown."""
    # Startup
    scheduler_manager = get_scheduler_manager()
    scheduler_manager.start()
    
    try:
        yield
    finally:
        # Shutdown
        scheduler_manager.shutdown()


app = FastAPI(
    title="Pavlov API",
    description="AI-assisted investment decision support system",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Set up CORS middleware
setup_cors_middleware(app)

# Include API v1 router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Legacy health check endpoint for backward compatibility."""
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Pavlov API is running", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
