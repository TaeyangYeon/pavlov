"""
Unit tests for US Analysis Job.
Tests US market daily analysis job functionality.
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from freezegun import freeze_time
import pytz

from app.scheduler.jobs.us_analysis_job import run_us_analysis


KST = pytz.timezone("Asia/Seoul")


@pytest.mark.asyncio
class TestUSAnalysisJob:
    """Test US market daily analysis job."""

    @freeze_time("2024-01-16 07:10:00", tz_offset=9)  # KST Tuesday
    async def test_us_job_skips_if_already_executed(self):
        """Test that job skips if already executed for target date."""
        mock_session = AsyncMock()
        mock_log_repo = AsyncMock()
        mock_log_repo.exists.return_value = True  # Already executed
        
        mock_container = MagicMock()
        mock_container.analysis_log_repository.return_value = mock_log_repo
        
        with patch('app.scheduler.jobs.us_analysis_job.AsyncSessionLocal') as mock_session_local, \
             patch('app.scheduler.jobs.us_analysis_job.get_container', return_value=mock_container), \
             patch('app.scheduler.jobs.us_analysis_job.get_settings') as mock_settings, \
             patch('builtins.print') as mock_print:
            
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_settings.return_value.us_tickers = ["AAPL"]

            await run_us_analysis()

            # Verify exists was called with PREVIOUS DAY date (Jan 15)
            mock_log_repo.exists.assert_called_once_with("US", date(2024, 1, 15))
            
            # Verify skip message was printed
            skip_calls = [call for call in mock_print.call_args_list 
                         if "US analysis already executed" in str(call)]
            assert len(skip_calls) == 1

    @freeze_time("2024-01-16 07:10:00", tz_offset=9)  # KST Tuesday
    async def test_us_job_runs_full_pipeline_on_miss(self):
        """Test that job runs full pipeline when not executed."""
        mock_session = AsyncMock()
        mock_log_repo = AsyncMock()
        mock_log_repo.exists.return_value = False  # Not executed yet
        
        mock_market_service = AsyncMock()
        mock_market_service.fetch_and_cache.return_value = {
            "open": 150, "high": 155, "low": 148, "close": 152, "volume": 5000
        }
        
        mock_filter_chain = AsyncMock()
        mock_filter_chain.apply.return_value = [{"ticker": "AAPL", "close": 152}]
        
        mock_ai_pipeline = AsyncMock()
        mock_ai_output = MagicMock()
        mock_ai_pipeline.run.return_value = mock_ai_output
        
        mock_strategy_engine = AsyncMock()
        mock_strategy_result = MagicMock()
        mock_strategy_result.total_tickers_analyzed = 1
        mock_strategy_engine.run.return_value = mock_strategy_result
        
        mock_container = MagicMock()
        mock_container.analysis_log_repository.return_value = mock_log_repo
        mock_container.market_data_service.return_value = mock_market_service
        mock_container.filter_chain.return_value = mock_filter_chain
        mock_container.analysis_pipeline.return_value = mock_ai_pipeline
        mock_container.strategy_integration_engine.return_value = mock_strategy_engine
        
        mock_settings = MagicMock()
        mock_settings.us_tickers = ["AAPL"]
        
        with patch('app.scheduler.jobs.us_analysis_job.AsyncSessionLocal') as mock_session_local, \
             patch('app.scheduler.jobs.us_analysis_job.get_container', return_value=mock_container), \
             patch('app.scheduler.jobs.us_analysis_job.get_settings', return_value=mock_settings), \
             patch('builtins.print'):
            
            mock_session_local.return_value.__aenter__.return_value = mock_session

            await run_us_analysis()

            # Verify market data was fetched for PREVIOUS DAY (Jan 15)
            mock_market_service.fetch_and_cache.assert_called_once_with(
                "AAPL", "US", date(2024, 1, 15)
            )
            
            # Verify full pipeline was executed
            mock_filter_chain.apply.assert_called_once()
            mock_ai_pipeline.run.assert_called_once()
            mock_strategy_engine.run.assert_called_once()

    @freeze_time("2024-01-03 07:10:00", tz_offset=9)  # KST Wednesday 
    async def test_us_job_uses_previous_day_date(self):
        """Test that US job uses previous day date correctly."""
        mock_session = AsyncMock()
        mock_log_repo = AsyncMock()
        mock_log_repo.exists.return_value = True  # Skip execution
        
        mock_container = MagicMock()
        mock_container.analysis_log_repository.return_value = mock_log_repo
        
        with patch('app.scheduler.jobs.us_analysis_job.AsyncSessionLocal') as mock_session_local, \
             patch('app.scheduler.jobs.us_analysis_job.get_container', return_value=mock_container), \
             patch('app.scheduler.jobs.us_analysis_job.get_settings') as mock_settings, \
             patch('builtins.print'):
            
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_settings.return_value.us_tickers = ["AAPL"]

            await run_us_analysis()

            # 07:10 KST 2024-01-03 should use 2024-01-02 (previous day)
            mock_log_repo.exists.assert_called_once_with("US", date(2024, 1, 2))

    @freeze_time("2024-01-16 07:10:00", tz_offset=9)  # KST
    async def test_us_job_marks_executed_on_success(self):
        """Test that job completes successfully without explicit executed=True marking."""
        mock_session = AsyncMock()
        mock_log_repo = AsyncMock()
        mock_log_repo.exists.return_value = False
        
        mock_market_service = AsyncMock()
        mock_market_service.fetch_and_cache.return_value = {"close": 152}
        
        mock_filter_chain = AsyncMock()
        mock_filter_chain.apply.return_value = [{"ticker": "AAPL"}]
        
        mock_ai_pipeline = AsyncMock()
        mock_strategy_engine = AsyncMock()
        mock_strategy_result = MagicMock()
        mock_strategy_result.total_tickers_analyzed = 1
        mock_strategy_engine.run.return_value = mock_strategy_result
        
        mock_container = MagicMock()
        mock_container.analysis_log_repository.return_value = mock_log_repo
        mock_container.market_data_service.return_value = mock_market_service
        mock_container.filter_chain.return_value = mock_filter_chain
        mock_container.analysis_pipeline.return_value = mock_ai_pipeline
        mock_container.strategy_integration_engine.return_value = mock_strategy_engine
        
        mock_settings = MagicMock()
        mock_settings.us_tickers = ["AAPL"]
        
        with patch('app.scheduler.jobs.us_analysis_job.AsyncSessionLocal') as mock_session_local, \
             patch('app.scheduler.jobs.us_analysis_job.get_container', return_value=mock_container), \
             patch('app.scheduler.jobs.us_analysis_job.get_settings', return_value=mock_settings), \
             patch('builtins.print'):
            
            mock_session_local.return_value.__aenter__.return_value = mock_session

            await run_us_analysis()

            # Strategy engine should complete successfully
            mock_strategy_engine.run.assert_called_once()

    @freeze_time("2024-01-16 07:10:00", tz_offset=9)  # KST
    async def test_us_job_failure_does_not_affect_kr(self):
        """Test that US job failure is isolated (exception propagated to runner)."""
        mock_session = AsyncMock()
        mock_log_repo = AsyncMock()
        mock_log_repo.exists.return_value = False
        
        mock_market_service = AsyncMock()
        mock_market_service.fetch_and_cache.return_value = {"close": 152}
        
        mock_filter_chain = AsyncMock()
        mock_filter_chain.apply.return_value = [{"ticker": "AAPL"}]
        
        mock_ai_pipeline = AsyncMock()
        mock_ai_pipeline.run.side_effect = Exception("US AI call failed")
        
        mock_container = MagicMock()
        mock_container.analysis_log_repository.return_value = mock_log_repo
        mock_container.market_data_service.return_value = mock_market_service
        mock_container.filter_chain.return_value = mock_filter_chain
        mock_container.analysis_pipeline.return_value = mock_ai_pipeline
        mock_container.strategy_integration_engine.return_value = AsyncMock()
        
        mock_settings = MagicMock()
        mock_settings.us_tickers = ["AAPL"]
        
        with patch('app.scheduler.jobs.us_analysis_job.AsyncSessionLocal') as mock_session_local, \
             patch('app.scheduler.jobs.us_analysis_job.get_container', return_value=mock_container), \
             patch('app.scheduler.jobs.us_analysis_job.get_settings', return_value=mock_settings), \
             patch('builtins.print'), \
             pytest.raises(Exception, match="US AI call failed"):
            
            mock_session_local.return_value.__aenter__.return_value = mock_session

            await run_us_analysis()

            # Verify failure was logged with previous day date
            mock_log_repo.save.assert_called_once_with(
                date=date(2024, 1, 15),  # Previous day
                market="US",
                executed=False,
                error_message="US AI call failed"
            )

    @freeze_time("2024-01-16 07:10:00", tz_offset=9)  # KST
    async def test_us_job_handles_empty_market_data(self):
        """Test US job handles case with no market data."""
        mock_session = AsyncMock()
        mock_log_repo = AsyncMock()
        mock_log_repo.exists.return_value = False
        
        mock_market_service = AsyncMock()
        mock_market_service.fetch_and_cache.return_value = None  # No data
        
        mock_filter_chain = AsyncMock()
        mock_filter_chain.apply.return_value = []  # Empty after filtering
        
        mock_ai_pipeline = AsyncMock()
        mock_strategy_engine = AsyncMock()
        mock_strategy_result = MagicMock()
        mock_strategy_result.total_tickers_analyzed = 0
        mock_strategy_engine.run.return_value = mock_strategy_result
        
        mock_container = MagicMock()
        mock_container.analysis_log_repository.return_value = mock_log_repo
        mock_container.market_data_service.return_value = mock_market_service
        mock_container.filter_chain.return_value = mock_filter_chain
        mock_container.analysis_pipeline.return_value = mock_ai_pipeline
        mock_container.strategy_integration_engine.return_value = mock_strategy_engine
        
        mock_settings = MagicMock()
        mock_settings.us_tickers = ["AAPL"]
        
        with patch('app.scheduler.jobs.us_analysis_job.AsyncSessionLocal') as mock_session_local, \
             patch('app.scheduler.jobs.us_analysis_job.get_container', return_value=mock_container), \
             patch('app.scheduler.jobs.us_analysis_job.get_settings', return_value=mock_settings), \
             patch('builtins.print'):
            
            mock_session_local.return_value.__aenter__.return_value = mock_session

            await run_us_analysis()

            # Job should still complete with empty data
            mock_filter_chain.apply.assert_called_once_with([])
            mock_ai_pipeline.run.assert_called_once()
            mock_strategy_engine.run.assert_called_once()