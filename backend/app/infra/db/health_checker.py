"""
Database health checker for monitoring connection pool and query performance.
"""

import asyncio
import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.domain.shared.exceptions import DatabaseError
from app.domain.shared.result import Result
from app.infra.db.base import AsyncSessionLocal, engine


class DatabaseHealthChecker:
    """
    Database health checker with connection pool monitoring.
    Provides health status, latency metrics, and connection pool stats.
    """

    def __init__(self, timeout_seconds: int = 5, max_retries: int = 3):
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    async def check_health(self) -> Result[dict[str, Any]]:
        """
        Perform comprehensive database health check.
        
        Returns:
            Result[Dict]: Health status with metrics or error details
        """
        start_time = time.time()

        try:
            # Test basic connectivity with timeout
            await asyncio.wait_for(
                self._test_connectivity(),
                timeout=self.timeout_seconds
            )

            # Get connection pool status
            pool_status = self._get_pool_status()

            # Calculate latency
            latency_ms = round((time.time() - start_time) * 1000, 2)

            # Determine overall health
            is_healthy = self._evaluate_health(pool_status, latency_ms)

            return Result.ok({
                "status": "healthy" if is_healthy else "degraded",
                "latency_ms": latency_ms,
                "timestamp": start_time,
                "pool": pool_status,
                "timeout_seconds": self.timeout_seconds
            })

        except TimeoutError:
            return Result.fail(f"Database health check timeout after {self.timeout_seconds}s")
        except DatabaseError as e:
            return Result.fail(f"Database health check failed: {e}")
        except Exception as e:
            return Result.fail(f"Unexpected error during health check: {str(e)}")

    async def check_health_with_retry(self) -> Result[dict[str, Any]]:
        """
        Health check with retry logic for transient failures.
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                result = await self.check_health()
                if result.is_ok():
                    # Add retry context to successful result
                    health_data = result.unwrap()
                    health_data["attempts"] = attempt + 1
                    return Result.ok(health_data)
                else:
                    last_error = result.error
                    if attempt < self.max_retries - 1:
                        # Exponential backoff: 0.5s, 1s, 2s
                        await asyncio.sleep(0.5 * (2 ** attempt))
            except Exception as e:
                last_error = str(e)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(0.5 * (2 ** attempt))

        return Result.fail(f"Database health check failed after {self.max_retries} attempts: {last_error}")

    async def _test_connectivity(self) -> None:
        """
        Test basic database connectivity with a simple query.
        
        Raises:
            DatabaseError: If connectivity test fails
        """
        try:
            async with AsyncSessionLocal() as session:
                # Simple query to test connectivity
                result = await session.execute(text("SELECT 1 as health_check"))
                row = result.fetchone()

                if row is None or row[0] != 1:
                    raise DatabaseError(
                        operation="health_check",
                        reason="Health check query returned unexpected result"
                    )

        except SQLAlchemyError as e:
            raise DatabaseError(
                operation="health_check",
                reason=f"Database connectivity test failed: {str(e)}"
            )

    def _get_pool_status(self) -> dict[str, Any]:
        """
        Get connection pool status and metrics.
        """
        pool = engine.pool

        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "utilization_percent": round(
                (pool.checkedout() / pool.size()) * 100, 2
            ) if pool.size() > 0 else 0
        }

    def _evaluate_health(self, pool_status: dict[str, Any], latency_ms: float) -> bool:
        """
        Evaluate overall database health based on metrics.
        
        Criteria:
        - Pool utilization < 80%
        - No overflow connections
        - Latency < 1000ms
        """
        utilization_ok = pool_status["utilization_percent"] < 80
        no_overflow = pool_status["overflow"] == 0
        latency_ok = latency_ms < 1000  # 1 second threshold

        return utilization_ok and no_overflow and latency_ok


class StartupHealthChecker:
    """
    Database health checker specifically for application startup.
    Blocks startup if database is not available.
    """

    def __init__(self, max_startup_retries: int = 10, retry_delay: int = 2):
        self.max_startup_retries = max_startup_retries
        self.retry_delay = retry_delay
        self.health_checker = DatabaseHealthChecker(timeout_seconds=10)

    async def ensure_database_ready(self) -> None:
        """
        Ensure database is ready before application startup.
        Blocks startup until database is available or max retries exceeded.
        
        Raises:
            DatabaseError: If database is not available after max retries
        """
        print("Checking database health during startup...")

        for attempt in range(1, self.max_startup_retries + 1):
            print(f"Database health check attempt {attempt}/{self.max_startup_retries}")

            result = await self.health_checker.check_health()

            if result.is_ok():
                health_data = result.unwrap()
                print(f"✅ Database ready! Status: {health_data['status']}, "
                      f"Latency: {health_data['latency_ms']}ms")
                return

            print(f"❌ Database not ready: {result.error}")

            if attempt < self.max_startup_retries:
                print(f"Retrying in {self.retry_delay} seconds...")
                await asyncio.sleep(self.retry_delay)

        # All retries exhausted
        raise DatabaseError(
            operation="startup_check",
            reason=f"Database not available after {self.max_startup_retries} attempts"
        )
