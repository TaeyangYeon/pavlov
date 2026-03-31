from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI
from sqlalchemy import select

from app.api.middleware.cors import setup_cors_middleware
from app.api.middleware.error_handlers import setup_error_handlers
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.container import get_container
from app.infra.db.base import AsyncSessionLocal
from app.infra.db.health_checker import StartupHealthChecker
from app.infra.db.models.user import User
from app.scheduler.recovery import RecoveryManager
from app.scheduler.scheduler import get_scheduler_manager

settings = get_settings()

STUB_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan with health checks and error handling:
    0. Database health check (startup gate)
    1. Ensure stub user exists
    2. Run missed execution recovery
    3. Start scheduler
    4. App runs
    5. Stop scheduler
    """
    # Step 0: Database health check (startup gate)
    print("[App] Performing startup health checks...")
    try:
        startup_health_checker = StartupHealthChecker(max_startup_retries=10, retry_delay=2)
        await startup_health_checker.ensure_database_ready()
        print("[App] ✅ Database health check passed")
    except Exception as e:
        print(f"[App] ❌ Database health check failed: {e}")
        print("[App] Application startup aborted due to unhealthy database")
        raise  # Block application startup

    # Step 1: Ensure stub user exists
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(
                User.id == STUB_USER_ID
            )
            result = await session.execute(stmt)
            if not result.scalar_one_or_none():
                stub_user = User(
                    id=STUB_USER_ID,
                    email="stub@pavlov.local",
                    is_active=True,
                )
                session.add(stub_user)
                await session.commit()
                print("[App] Stub user created")
    except Exception as e:
        print(f"[App] Stub user check failed: {e}")

    # Step 2: Recovery on startup
    print("[App] Checking for missed executions...")
    try:
        async with AsyncSessionLocal() as session:
            container = get_container()
            kr_repo = container.analysis_log_repository(session)
            us_repo = container.analysis_log_repository(session)
            recovery = RecoveryManager(kr_repo, us_repo)
            results = await recovery.check_and_recover()
            kr_result = results["kr"]
            us_result = results["us"]
            print(
                f"[App] Recovery complete — "
                f"KR: {'recovered' if kr_result['recovered'] else 'none'}, "
                f"US: {'recovered' if us_result['recovered'] else 'none'}"
            )
    except Exception as e:
        print(f"[App] Recovery check failed (non-fatal): {e}")

    # Step 3: Start scheduler
    if settings.scheduler_enabled:
        scheduler_manager = get_scheduler_manager()
        scheduler_manager.start()
        print("[App] Scheduler started")

    print("[App] 🚀 Application startup complete - all systems operational")

    try:
        yield  # App is running
    finally:
        # Step 4: Stop scheduler
        print("[App] 🛑 Application shutdown initiated")
        if settings.scheduler_enabled:
            scheduler_manager = get_scheduler_manager()
            try:
                scheduler_manager.shutdown()
                print("[App] Scheduler stopped")
            except Exception as e:
                print(f"[App] Error stopping scheduler: {e}")
        print("[App] Application shutdown complete")


app = FastAPI(
    title="Pavlov API",
    description="AI-assisted investment decision support system",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Set up CORS middleware
setup_cors_middleware(app)

# Set up global error handlers
setup_error_handlers(app)

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
