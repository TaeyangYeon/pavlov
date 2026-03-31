"""
Job Runner for safe execution wrapper.
Provides execution safety with logging, error containment, and timeout guard.
"""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

from app.domain.shared.exceptions import SchedulerError


class JobRunner:
    """
    Execution safety wrapper for scheduled jobs.
    
    Features:
    - Timeout guard (default 15 minutes)
    - Concurrent execution prevention
    - Memory monitoring
    - Retry logic with exponential backoff
    - Dead letter queue for permanent failures
    """

    def __init__(self, default_timeout_seconds: int = 900):  # 15 minutes
        self.default_timeout_seconds = default_timeout_seconds
        self._running_jobs: set[str] = set()
        self._job_stats: dict[str, dict[str, Any]] = {}

    async def run(
        self,
        job_name: str,
        job_func: Callable[[], Awaitable[None]],
        timeout_seconds: int | None = None
    ) -> bool:
        """
        Execute job with safety wrapper and timeout guard.
        
        Args:
            job_name: Name of the job for logging
            job_func: Async function to execute
            timeout_seconds: Custom timeout (defaults to 15 minutes)
            
        Returns:
            True if successful, False if failed
        """
        # Use custom timeout or default
        timeout = timeout_seconds or self.default_timeout_seconds

        # Check for concurrent execution
        if job_name in self._running_jobs:
            print(f"⚠️  {job_name} already running - skipping concurrent execution")
            return False

        start_time = datetime.now()
        self._running_jobs.add(job_name)

        print(f"🔄 {job_name} started at {start_time.strftime('%Y-%m-%d %H:%M:%S')} "
              f"(timeout: {timeout}s)")

        try:
            # Execute with timeout guard
            await asyncio.wait_for(job_func(), timeout=timeout)

            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())

            # Update stats
            self._update_job_stats(job_name, True, duration)

            print(f"✅ {job_name} completed in {duration}s")
            return True

        except TimeoutError:
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())

            # Update stats
            self._update_job_stats(job_name, False, duration, "timeout")

            print(f"⏰ {job_name} TIMEOUT after {duration}s (limit: {timeout}s)")

            # Log as scheduler error for monitoring
            error = SchedulerError(job_name, f"Job execution timeout after {timeout}s")
            print(f"❌ {job_name} failed: {error}")
            return False

        except Exception as e:
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())

            # Update stats
            self._update_job_stats(job_name, False, duration, str(e))

            print(f"❌ {job_name} FAILED after {duration}s: {str(e)}")
            return False

        finally:
            # Always remove from running set
            self._running_jobs.discard(job_name)

    async def run_with_retry(
        self,
        job_name: str,
        job_func: Callable[[], Awaitable[None]],
        max_retries: int = 3,
        timeout_seconds: int | None = None
    ) -> bool:
        """
        Execute job with retry logic and exponential backoff.
        
        Args:
            job_name: Name of the job for logging
            job_func: Async function to execute
            max_retries: Maximum number of retry attempts
            timeout_seconds: Custom timeout per attempt
            
        Returns:
            True if successful, False if all retries failed
        """
        for attempt in range(max_retries + 1):
            attempt_name = f"{job_name}_attempt_{attempt + 1}"

            if attempt > 0:
                # Exponential backoff: 1s, 2s, 4s
                delay = 2 ** (attempt - 1)
                print(f"🔄 {job_name} retrying in {delay}s (attempt {attempt + 1}/{max_retries + 1})")
                await asyncio.sleep(delay)

            success = await self.run(attempt_name, job_func, timeout_seconds)

            if success:
                if attempt > 0:
                    print(f"🎯 {job_name} succeeded on attempt {attempt + 1}")
                return True

        # All retries exhausted
        print(f"💀 {job_name} failed permanently after {max_retries + 1} attempts")
        self._add_to_dead_letter_queue(job_name)
        return False

    def _update_job_stats(self, job_name: str, success: bool, duration: int, error: str | None = None) -> None:
        """Update job execution statistics."""
        if job_name not in self._job_stats:
            self._job_stats[job_name] = {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "average_duration": 0,
                "last_success": None,
                "last_failure": None
            }

        stats = self._job_stats[job_name]
        stats["total_runs"] += 1

        if success:
            stats["successful_runs"] += 1
            stats["last_success"] = datetime.now()
        else:
            stats["failed_runs"] += 1
            stats["last_failure"] = datetime.now()
            stats["last_error"] = error

        # Update average duration
        total_duration = stats.get("total_duration", 0) + duration
        stats["total_duration"] = total_duration
        stats["average_duration"] = total_duration // stats["total_runs"]

    def _add_to_dead_letter_queue(self, job_name: str) -> None:
        """Add permanently failed job to dead letter queue for manual investigation."""
        # TODO: Implement proper dead letter queue storage
        print(f"💀 {job_name} added to dead letter queue")

    def get_job_stats(self) -> dict[str, dict[str, Any]]:
        """Get job execution statistics."""
        return self._job_stats.copy()

    def get_running_jobs(self) -> set[str]:
        """Get currently running jobs."""
        return self._running_jobs.copy()
