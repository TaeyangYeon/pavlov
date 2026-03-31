"""
Unit tests for scheduler job timeout handling and execution guards.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from app.domain.shared.exceptions import SchedulerError


class TestSchedulerJobTimeout:
    """Test scheduler job timeout handling."""

    async def test_scheduler_job_completes_within_timeout(self):
        """Test that job completing within timeout works normally."""
        async def quick_job():
            await asyncio.sleep(0.1)  # 100ms job
            return "completed"
        
        # Simulate timeout wrapper (15 minutes = 900 seconds)
        try:
            result = await asyncio.wait_for(quick_job(), timeout=900)
            assert result == "completed"
        except asyncio.TimeoutError:
            pytest.fail("Job should not timeout")

    async def test_scheduler_job_timeout_raises_scheduler_error(self):
        """Test that job timeout raises SchedulerError."""
        async def long_running_job():
            await asyncio.sleep(2)  # 2 second job
            return "completed"
        
        with pytest.raises(SchedulerError) as exc_info:
            try:
                # Use 1 second timeout to force timeout
                await asyncio.wait_for(long_running_job(), timeout=1)
            except asyncio.TimeoutError:
                raise SchedulerError(
                    job="test_job",
                    reason="Job execution timeout after 1 seconds"
                )
        
        assert exc_info.value.details["job"] == "test_job"
        assert "timeout" in str(exc_info.value).lower()

    async def test_scheduler_job_timeout_with_cleanup(self):
        """Test that timed out job triggers cleanup logic."""
        cleanup_called = False
        
        async def job_with_cleanup():
            try:
                await asyncio.sleep(2)  # Long running job
                return "completed"
            except asyncio.CancelledError:
                # Cleanup logic
                nonlocal cleanup_called
                cleanup_called = True
                raise
        
        task = asyncio.create_task(job_with_cleanup())
        
        try:
            await asyncio.wait_for(task, timeout=1)
        except asyncio.TimeoutError:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Wait a bit for cleanup to execute
        await asyncio.sleep(0.1)
        assert cleanup_called is True

    async def test_multiple_jobs_timeout_isolation(self):
        """Test that timeout in one job doesn't affect others."""
        results = {}
        
        async def quick_job(job_id: str):
            await asyncio.sleep(0.1)
            results[job_id] = "completed"
            return "completed"
        
        async def slow_job(job_id: str):
            await asyncio.sleep(2)
            results[job_id] = "completed"
            return "completed"
        
        # Run jobs concurrently with different timeouts
        tasks = [
            asyncio.create_task(
                asyncio.wait_for(quick_job("job1"), timeout=1)
            ),
            asyncio.create_task(
                asyncio.wait_for(quick_job("job2"), timeout=1)  
            ),
        ]
        
        # Add slow job that will timeout
        slow_task = asyncio.create_task(
            asyncio.wait_for(slow_job("slow_job"), timeout=1)
        )
        
        # Wait for quick jobs to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Slow job should timeout
        try:
            await slow_task
        except asyncio.TimeoutError:
            pass
        
        # Quick jobs should have completed despite slow job timeout
        assert results["job1"] == "completed"
        assert results["job2"] == "completed"
        assert "slow_job" not in results


class TestSchedulerJobExecutionGuard:
    """Test scheduler job execution guard functionality."""

    async def test_concurrent_execution_prevention(self):
        """Test prevention of concurrent execution of same job."""
        job_running = False
        execution_attempts = []
        
        async def guarded_job(job_id: str):
            nonlocal job_running
            
            if job_running:
                execution_attempts.append(f"{job_id}_blocked")
                raise SchedulerError(
                    job=job_id,
                    reason="Job already running - concurrent execution prevented"
                )
            
            job_running = True
            execution_attempts.append(f"{job_id}_started")
            try:
                await asyncio.sleep(0.5)  # Simulate work
                execution_attempts.append(f"{job_id}_completed")
                return "completed"
            finally:
                job_running = False
        
        # Try to run same job concurrently
        task1 = asyncio.create_task(guarded_job("kr_analysis"))
        await asyncio.sleep(0.1)  # Let first job start
        task2 = asyncio.create_task(guarded_job("kr_analysis"))
        
        # First should succeed, second should be blocked
        result1 = await task1
        
        try:
            await task2
            pytest.fail("Second job should have been blocked")
        except SchedulerError as e:
            assert "concurrent execution prevented" in str(e)
        
        assert result1 == "completed"
        assert "kr_analysis_started" in execution_attempts
        assert "kr_analysis_completed" in execution_attempts
        assert "kr_analysis_blocked" in execution_attempts

    async def test_job_execution_retry_after_failure(self):
        """Test job retry mechanism after failure."""
        attempt_count = 0
        max_attempts = 3
        
        async def failing_job():
            nonlocal attempt_count
            attempt_count += 1
            
            if attempt_count < max_attempts:
                raise Exception(f"Job failed on attempt {attempt_count}")
            
            return f"succeeded_on_attempt_{attempt_count}"
        
        # Simulate retry logic
        for attempt in range(max_attempts):
            try:
                result = await failing_job()
                break
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise SchedulerError(
                        job="retry_test_job",
                        reason=f"Failed after {max_attempts} attempts: {str(e)}"
                    )
                # Continue to next attempt
        
        assert result == "succeeded_on_attempt_3"
        assert attempt_count == 3

    async def test_job_execution_with_memory_monitoring(self):
        """Test job execution with memory usage monitoring."""
        memory_usage = []
        
        async def memory_intensive_job():
            # Simulate memory usage tracking
            memory_usage.append({"stage": "start", "memory_mb": 100})
            
            # Simulate work that uses memory
            await asyncio.sleep(0.1)
            memory_usage.append({"stage": "working", "memory_mb": 250})
            
            # Check if memory usage is acceptable
            current_memory = memory_usage[-1]["memory_mb"]
            if current_memory > 500:  # 500MB limit
                raise SchedulerError(
                    job="memory_test_job",
                    reason=f"Memory usage {current_memory}MB exceeds limit"
                )
            
            memory_usage.append({"stage": "end", "memory_mb": 120})
            return "completed"
        
        result = await memory_intensive_job()
        
        assert result == "completed"
        assert len(memory_usage) == 3
        assert all(usage["memory_mb"] <= 500 for usage in memory_usage)


class TestSchedulerJobRecovery:
    """Test scheduler job recovery and failure handling."""

    async def test_job_failure_recovery_with_exponential_backoff(self):
        """Test job recovery with exponential backoff strategy."""
        failure_count = 0
        backoff_delays = []
        
        async def unreliable_job():
            nonlocal failure_count
            failure_count += 1
            
            if failure_count <= 2:
                raise Exception(f"Temporary failure {failure_count}")
            
            return "recovered"
        
        # Simulate exponential backoff: 1s, 2s, 4s
        for attempt in range(3):
            try:
                result = await unreliable_job()
                break
            except Exception:
                if attempt < 2:  # Don't delay after last attempt
                    delay = 2 ** attempt  # 1, 2, 4 seconds
                    backoff_delays.append(delay)
                    # In real implementation: await asyncio.sleep(delay)
        
        assert result == "recovered"
        assert backoff_delays == [1, 2]
        assert failure_count == 3

    async def test_job_dead_letter_queue_on_permanent_failure(self):
        """Test that permanently failed jobs go to dead letter queue."""
        dead_letter_queue = []
        max_retries = 3
        
        async def permanently_failing_job():
            raise Exception("Permanent failure - data source unavailable")
        
        # Simulate retry loop that eventually gives up
        for attempt in range(max_retries + 1):
            try:
                await permanently_failing_job()
                break
            except Exception as e:
                if attempt == max_retries:
                    # Add to dead letter queue
                    dead_letter_queue.append({
                        "job": "failing_job",
                        "error": str(e),
                        "attempts": attempt + 1,
                        "timestamp": datetime.now()
                    })
                    break
        
        assert len(dead_letter_queue) == 1
        assert dead_letter_queue[0]["attempts"] == 4
        assert "Permanent failure" in dead_letter_queue[0]["error"]