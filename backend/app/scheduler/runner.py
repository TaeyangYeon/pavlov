"""
Job Runner for safe execution wrapper.
Provides execution safety with logging and error containment.
"""

from collections.abc import Awaitable, Callable
from datetime import datetime


class JobRunner:
    """Execution safety wrapper for scheduled jobs."""

    async def run(self, job_name: str, job_func: Callable[[], Awaitable[None]]) -> bool:
        """
        Execute job with safety wrapper.
        
        Args:
            job_name: Name of the job for logging
            job_func: Async function to execute
            
        Returns:
            True if successful, False if failed
        """
        start_time = datetime.now()
        print(f"🔄 {job_name} started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            await job_func()

            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            print(f"✅ {job_name} completed in {duration}s")
            return True

        except Exception as e:
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            print(f"❌ {job_name} FAILED after {duration}s: {str(e)}")
            return False
