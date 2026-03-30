"""
Unit tests for KR Analysis Job.
Tests KR market daily analysis job functionality.
"""

import pytest
from datetime import datetime, date
from unittest.mock import AsyncMock, patch, MagicMock
from freezegun import freeze_time
import pytz

from app.scheduler.jobs.kr_analysis_job import run_kr_analysis


KST = pytz.timezone("Asia/Seoul")


@pytest.mark.asyncio
class TestKRAnalysisJob:
    """Test KR market daily analysis job."""

    @freeze_time("2024-01-15 16:10:00", tz_offset=9)  # KST
    async def test_kr_job_skips_if_already_executed_today(self):
        """Test that job skips if already executed today."""
        mock_session = AsyncMock()
        mock_log_repo = AsyncMock()
        mock_log_repo.exists.return_value = True  # Already executed
        
        mock_container = MagicMock()
        mock_container.analysis_log_repository.return_value = mock_log_repo
        
        with patch('app.scheduler.jobs.kr_analysis_job.AsyncSessionLocal') as mock_session_local, \
             patch('app.scheduler.jobs.kr_analysis_job.get_container', return_value=mock_container), \
             patch('app.scheduler.jobs.kr_analysis_job.get_settings') as mock_settings, \
             patch('builtins.print') as mock_print:
            
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_settings.return_value.kr_tickers = ["005930"]

            await run_kr_analysis()

            # Verify exists was called with correct parameters
            mock_log_repo.exists.assert_called_once_with("KR", date(2024, 1, 15))
            
            # Verify skip message was printed
            skip_calls = [call for call in mock_print.call_args_list 
                         if "KR analysis already executed" in str(call)]
            assert len(skip_calls) == 1
            
            # Verify market data service was NOT called
            assert not mock_container.market_data_service.called

    @freeze_time("2024-01-15 16:10:00", tz_offset=9)  # KST
    async def test_kr_job_runs_full_pipeline_on_miss(self):
        """Test that job runs full pipeline when not executed."""
        mock_session = AsyncMock()
        mock_log_repo = AsyncMock()
        mock_log_repo.exists.return_value = False  # Not executed yet
        
        mock_market_service = AsyncMock()
        mock_market_service.fetch_and_cache.return_value = {
            "open": 100, "high": 110, "low": 95, "close": 105, "volume": 1000
        }
        
        mock_indicator_engine = AsyncMock()
        mock_filter_chain = AsyncMock()
        mock_filter_chain.apply.return_value = [{"ticker": "005930", "close": 105}]
        
        mock_ai_pipeline = AsyncMock()
        mock_ai_output = MagicMock()
        mock_ai_pipeline.run.return_value = mock_ai_output
        
        mock_strategy_engine = AsyncMock()
        mock_strategy_result = MagicMock()
        mock_strategy_result.total_tickers_analyzed = 1
        mock_strategy_result.changed_count = 1
        mock_strategy_engine.run.return_value = mock_strategy_result
        
        mock_container = MagicMock()
        mock_container.analysis_log_repository.return_value = mock_log_repo
        mock_container.market_data_service.return_value = mock_market_service
        mock_container.indicator_engine.return_value = mock_indicator_engine
        mock_container.filter_chain.return_value = mock_filter_chain
        mock_container.analysis_pipeline.return_value = mock_ai_pipeline
        mock_container.strategy_integration_engine.return_value = mock_strategy_engine
        
        mock_settings = MagicMock()
        mock_settings.kr_tickers = ["005930"]
        
        with patch('app.scheduler.jobs.kr_analysis_job.AsyncSessionLocal') as mock_session_local, \
             patch('app.scheduler.jobs.kr_analysis_job.get_container', return_value=mock_container), \
             patch('app.scheduler.jobs.kr_analysis_job.get_settings', return_value=mock_settings), \
             patch('builtins.print'):
            
            mock_session_local.return_value.__aenter__.return_value = mock_session

            await run_kr_analysis()

            # Verify full pipeline was called in order
            mock_market_service.fetch_and_cache.assert_called_once_with(
                "005930", "KR", date(2024, 1, 15)
            )
            mock_filter_chain.apply.assert_called_once()
            mock_ai_pipeline.run.assert_called_once()
            mock_strategy_engine.run.assert_called_once()

    @freeze_time("2024-01-15 16:10:00", tz_offset=9)  # KST  
    async def test_kr_job_marks_executed_on_success(self):
        """Test that job completion doesn't explicitly mark executed (handled by pipeline)."""
        mock_session = AsyncMock()
        mock_log_repo = AsyncMock()
        mock_log_repo.exists.return_value = False
        
        mock_market_service = AsyncMock()
        mock_market_service.fetch_and_cache.return_value = {
            "close": 105, "volume": 1000
        }
        
        mock_filter_chain = AsyncMock()
        mock_filter_chain.apply.return_value = [{"ticker": "005930"}]
        
        mock_ai_pipeline = AsyncMock()
        mock_strategy_engine = AsyncMock()
        mock_strategy_result = MagicMock()
        mock_strategy_result.total_tickers_analyzed = 1
        mock_strategy_result.changed_count = 0
        mock_strategy_engine.run.return_value = mock_strategy_result
        
        mock_container = MagicMock()
        mock_container.analysis_log_repository.return_value = mock_log_repo
        mock_container.market_data_service.return_value = mock_market_service
        mock_container.indicator_engine.return_value = AsyncMock()
        mock_container.filter_chain.return_value = mock_filter_chain
        mock_container.analysis_pipeline.return_value = mock_ai_pipeline
        mock_container.strategy_integration_engine.return_value = mock_strategy_engine
        
        mock_settings = MagicMock()
        mock_settings.kr_tickers = ["005930"]
        
        with patch('app.scheduler.jobs.kr_analysis_job.AsyncSessionLocal') as mock_session_local, \
             patch('app.scheduler.jobs.kr_analysis_job.get_container', return_value=mock_container), \
             patch('app.scheduler.jobs.kr_analysis_job.get_settings', return_value=mock_settings), \
             patch('builtins.print'):
            
            mock_session_local.return_value.__aenter__.return_value = mock_session

            await run_kr_analysis()

            # Strategy engine should complete successfully
            mock_strategy_engine.run.assert_called_once()

    @freeze_time("2024-01-15 16:10:00", tz_offset=9)  # KST
    async def test_kr_job_marks_not_executed_on_failure(self):
        """Test that job marks not executed on failure."""
        mock_session = AsyncMock()
        mock_log_repo = AsyncMock()
        mock_log_repo.exists.return_value = False
        
        mock_market_service = AsyncMock()
        mock_market_service.fetch_and_cache.return_value = {"close": 105}
        
        mock_filter_chain = AsyncMock()
        mock_filter_chain.apply.return_value = [{"ticker": "005930"}]
        
        mock_ai_pipeline = AsyncMock()
        mock_ai_pipeline.run.side_effect = Exception("AI call failed")
        
        mock_container = MagicMock()
        mock_container.analysis_log_repository.return_value = mock_log_repo
        mock_container.market_data_service.return_value = mock_market_service
        mock_container.indicator_engine.return_value = AsyncMock()
        mock_container.filter_chain.return_value = mock_filter_chain
        mock_container.analysis_pipeline.return_value = mock_ai_pipeline
        mock_container.strategy_integration_engine.return_value = AsyncMock()
        
        mock_settings = MagicMock()
        mock_settings.kr_tickers = ["005930"]
        
        with patch('app.scheduler.jobs.kr_analysis_job.AsyncSessionLocal') as mock_session_local, \
             patch('app.scheduler.jobs.kr_analysis_job.get_container', return_value=mock_container), \
             patch('app.scheduler.jobs.kr_analysis_job.get_settings', return_value=mock_settings), \
             patch('builtins.print'), \
             pytest.raises(Exception):
            
            mock_session_local.return_value.__aenter__.return_value = mock_session

            await run_kr_analysis()

            # Verify failure was logged to analysis_log
            mock_log_repo.save.assert_called_once_with(
                date=date(2024, 1, 15),
                market="KR",
                executed=False,
                error_message="AI call failed"
            )

    @freeze_time("2024-01-15 16:10:00", tz_offset=9)  # KST
    async def test_kr_job_uses_kst_date(self):
        """Test that job uses KST date correctly."""
        mock_session = AsyncMock()
        mock_log_repo = AsyncMock()
        mock_log_repo.exists.return_value = True  # Skip execution
        
        mock_container = MagicMock()
        mock_container.analysis_log_repository.return_value = mock_log_repo
        
        with patch('app.scheduler.jobs.kr_analysis_job.AsyncSessionLocal') as mock_session_local, \
             patch('app.scheduler.jobs.kr_analysis_job.get_container', return_value=mock_container), \
             patch('app.scheduler.jobs.kr_analysis_job.get_settings') as mock_settings, \
             patch('builtins.print'):
            
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_settings.return_value.kr_tickers = ["005930"]

            await run_kr_analysis()

            # Verify exists was called with KST date (2024-01-15)
            mock_log_repo.exists.assert_called_once_with("KR", date(2024, 1, 15))

    @freeze_time("2024-01-15 16:10:00", tz_offset=9)  # KST
    async def test_kr_job_handles_no_market_data(self):
        """Test that job handles case when no market data is available."""
        mock_session = AsyncMock()
        mock_log_repo = AsyncMock()
        mock_log_repo.exists.return_value = False
        
        mock_market_service = AsyncMock()
        mock_market_service.fetch_and_cache.return_value = None  # No data
        
        mock_container = MagicMock()
        mock_container.analysis_log_repository.return_value = mock_log_repo
        mock_container.market_data_service.return_value = mock_market_service
        
        mock_settings = MagicMock()
        mock_settings.kr_tickers = ["005930"]
        
        with patch('app.scheduler.jobs.kr_analysis_job.AsyncSessionLocal') as mock_session_local, \
             patch('app.scheduler.jobs.kr_analysis_job.get_container', return_value=mock_container), \
             patch('app.scheduler.jobs.kr_analysis_job.get_settings', return_value=mock_settings), \
             patch('builtins.print') as mock_print:
            
            mock_session_local.return_value.__aenter__.return_value = mock_session

            await run_kr_analysis()

            # Verify "no market data" message was printed
            no_data_calls = [call for call in mock_print.call_args_list 
                           if "no market data available" in str(call)]
            assert len(no_data_calls) == 1
            
            # Verify failure was logged
            mock_log_repo.save.assert_called_once_with(
                date=date(2024, 1, 15),
                market="KR",
                executed=False,
                error_message="No market data available"
            )