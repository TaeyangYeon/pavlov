"""
Comprehensive health check endpoint for system monitoring.
"""

import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.infra.db.health_checker import DatabaseHealthChecker

router = APIRouter()


class HealthService:
    """Service for comprehensive system health checks."""

    def __init__(self):
        self.db_health_checker = DatabaseHealthChecker(timeout_seconds=5)
        self.start_time = time.time()

    async def get_comprehensive_health(self) -> dict[str, Any]:
        """
        Get comprehensive health status for all system components.
        
        Returns:
            Dict with health status, individual component checks, and metrics
        """
        health_checks = {}
        overall_status = "healthy"

        # Check database health
        db_result = await self.db_health_checker.check_health()
        if db_result.is_ok():
            db_health = db_result.unwrap()
            health_checks["database"] = {
                "status": db_health["status"],
                "latency_ms": db_health["latency_ms"],
                "pool": db_health["pool"]
            }
            if db_health["status"] != "healthy":
                overall_status = "degraded"
        else:
            health_checks["database"] = {
                "status": "unhealthy",
                "error": db_result.error,
                "latency_ms": None
            }
            overall_status = "unhealthy"

        # Check external services (mock checks for now)
        health_checks["external_services"] = self._check_external_services()

        # Check scheduler health
        health_checks["scheduler"] = self._check_scheduler_health()

        # Check system resources
        health_checks["system"] = self._check_system_resources()

        # Determine overall status
        if any(check.get("status") == "unhealthy" for check in health_checks.values()):
            overall_status = "unhealthy"
        elif any(check.get("status") == "degraded" for check in health_checks.values()):
            overall_status = "degraded"

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime_seconds": int(time.time() - self.start_time),
            "version": "0.1.0",
            "environment": get_settings().APP_ENV,
            "checks": health_checks
        }

    def _check_external_services(self) -> dict[str, Any]:
        """Check health of external API dependencies."""
        # TODO: Implement actual external service health checks
        services = {
            "anthropic_api": {"status": "healthy", "latency_ms": 850},
            "kr_market_data": {"status": "healthy", "latency_ms": 200},
            "us_market_data": {"status": "healthy", "latency_ms": 350}
        }

        unhealthy_services = [name for name, info in services.items() if info["status"] != "healthy"]

        if unhealthy_services:
            status = "unhealthy" if len(unhealthy_services) > 1 else "degraded"
        else:
            status = "healthy"

        return {
            "status": status,
            "services": services,
            "healthy_count": len([s for s in services.values() if s["status"] == "healthy"]),
            "total_count": len(services)
        }

    def _check_scheduler_health(self) -> dict[str, Any]:
        """Check scheduler health and job statistics."""
        # TODO: Get actual scheduler statistics
        return {
            "status": "healthy",
            "active_jobs": 0,
            "completed_jobs_24h": 42,
            "failed_jobs_24h": 1,
            "average_job_duration_seconds": 25.5,
            "last_job_execution": "2024-01-15T10:30:00Z"
        }

    def _check_system_resources(self) -> dict[str, Any]:
        """Check system resource usage."""
        # TODO: Implement actual system resource monitoring
        return {
            "status": "healthy",
            "memory_usage_percent": 45.2,
            "cpu_usage_percent": 12.8,
            "disk_usage_percent": 34.1,
            "open_file_descriptors": 128,
            "active_connections": 5
        }


@router.get("/health", tags=["system"])
async def health_check():
    """Simple health check for load balancers."""
    return {"status": "ok", "version": "0.1.0", "environment": get_settings().APP_ENV}


@router.get("/health/detailed", tags=["system"])
async def detailed_health_check():
    """Comprehensive health check with component details."""
    health_service = HealthService()

    try:
        health_data = await health_service.get_comprehensive_health()

        # Return appropriate HTTP status based on health
        if health_data["status"] == "healthy":
            status_code = 200
        elif health_data["status"] == "degraded":
            status_code = 200  # Degraded but functional
        else:  # unhealthy
            status_code = 503  # Service Unavailable

        return JSONResponse(
            status_code=status_code,
            content=health_data
        )

    except Exception as e:
        error_response = {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": "Health check failed",
            "details": str(e)
        }

        return JSONResponse(
            status_code=503,
            content=error_response
        )


@router.get("/health/readiness", tags=["system"])
async def readiness_check():
    """Kubernetes-style readiness probe."""
    health_service = HealthService()

    try:
        db_result = await health_service.db_health_checker.check_health()

        if db_result.is_ok():
            db_health = db_result.unwrap()
            if db_health["status"] in ["healthy", "degraded"]:
                return {"status": "ready", "timestamp": datetime.utcnow().isoformat() + "Z"}

        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "reason": "Database not available",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "reason": f"Readiness check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
