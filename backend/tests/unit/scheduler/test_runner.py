"""
Unit tests for JobRunner.
Tests execution safety wrapper functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from app.scheduler.runner import JobRunner


@pytest.fixture
def job_runner():
    """Create JobRunner instance."""
    return JobRunner()


@pytest.mark.asyncio
class TestJobRunner:
    """Test JobRunner execution safety wrapper."""

    async def test_runner_logs_start_and_end(self, job_runner):
        """Test that runner logs start and end times."""
        async def mock_job():
            pass

        with patch('builtins.print') as mock_print:
            result = await job_runner.run("test_job", mock_job)

        assert result is True
        
        # Verify start log
        start_calls = [call for call in mock_print.call_args_list 
                      if "test_job started at" in str(call)]
        assert len(start_calls) == 1
        
        # Verify completion log
        complete_calls = [call for call in mock_print.call_args_list 
                         if "test_job completed in" in str(call)]
        assert len(complete_calls) == 1

    async def test_runner_catches_exception_does_not_propagate(self, job_runner):
        """Test that exceptions are caught and not re-raised."""
        async def failing_job():
            raise RuntimeError("Test error")

        with patch('builtins.print'):
            result = await job_runner.run("failing_job", failing_job)

        # Should return False on failure and not raise exception
        assert result is False

    async def test_runner_returns_true_on_success(self, job_runner):
        """Test that successful job returns True."""
        async def successful_job():
            pass

        with patch('builtins.print'):
            result = await job_runner.run("success_job", successful_job)

        assert result is True

    async def test_runner_records_duration(self, job_runner):
        """Test that runner calculates and logs duration."""
        async def mock_job():
            pass

        mock_start = datetime(2024, 1, 1, 12, 0, 0)
        mock_end = datetime(2024, 1, 1, 12, 0, 5)  # 5 seconds later

        with patch('builtins.print') as mock_print, \
             patch('app.scheduler.runner.datetime') as mock_datetime:
            
            mock_datetime.now.side_effect = [mock_start, mock_end]
            result = await job_runner.run("duration_test", mock_job)

        assert result is True
        
        # Check that duration was calculated (5 seconds)
        duration_calls = [call for call in mock_print.call_args_list 
                         if "completed in 5s" in str(call)]
        assert len(duration_calls) == 1

    async def test_runner_logs_failure_with_reason(self, job_runner):
        """Test that failure is logged with exception details."""
        async def failing_job():
            raise ValueError("Specific test error")

        with patch('builtins.print') as mock_print:
            result = await job_runner.run("error_job", failing_job)

        assert result is False
        
        # Verify error log contains exception message
        error_calls = [call for call in mock_print.call_args_list 
                      if "error_job FAILED" in str(call) and "Specific test error" in str(call)]
        assert len(error_calls) == 1