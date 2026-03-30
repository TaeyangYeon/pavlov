"""
Unit tests for RecoveryManager.
Tests all recovery scenarios including staleness cutoff, 
market isolation, and partial execution recovery.
"""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from freezegun import freeze_time

from app.infra.db.models.analysis_log import AnalysisLog
from app.scheduler.recovery import RecoveryManager


class TestRecoveryManager:
    """Test suite for RecoveryManager recovery scenarios."""

    @pytest.fixture
    def mock_kr_repo(self):
        """Mock KR analysis log repository."""
        mock_repo = AsyncMock()
        mock_repo.get_unexecuted = AsyncMock()
        return mock_repo

    @pytest.fixture
    def mock_us_repo(self):
        """Mock US analysis log repository."""
        mock_repo = AsyncMock()
        mock_repo.get_unexecuted = AsyncMock()
        return mock_repo

    @pytest.fixture
    def mock_settings(self):
        """Mock settings with max_recovery_days=3."""
        settings = MagicMock()
        settings.max_recovery_days = 3
        return settings

    @pytest.fixture
    def recovery_manager(self, mock_kr_repo, mock_us_repo, mock_settings):
        """Recovery manager with mocked dependencies."""
        manager = RecoveryManager(mock_kr_repo, mock_us_repo)
        # Override settings
        manager._settings = mock_settings
        return manager

    # ── SCENARIO 1: No missed executions ──

    @pytest.mark.asyncio
    async def test_recovery_does_nothing_when_no_missed(
        self, recovery_manager, mock_kr_repo, mock_us_repo, capfd
    ):
        """No missed executions → no recovery actions taken."""
        # Mock empty unexecuted lists for all checked dates
        mock_kr_repo.get_unexecuted.return_value = []
        mock_us_repo.get_unexecuted.return_value = []

        results = await recovery_manager.check_and_recover()

        assert results["kr"]["recovered"] is False
        assert results["kr"]["date"] is None
        assert results["kr"]["error"] is None
        assert results["us"]["recovered"] is False
        assert results["us"]["date"] is None
        assert results["us"]["error"] is None

        # Verify repository was called for date range
        assert mock_kr_repo.get_unexecuted.call_count >= 1
        assert mock_us_repo.get_unexecuted.call_count >= 1

        # Check console output
        captured = capfd.readouterr()
        assert "[Recovery] KR: no missed executions found" in captured.out
        assert "[Recovery] US: no missed executions found" in captured.out

    # ── SCENARIO 2: Single missed KR execution ──

    @pytest.mark.asyncio
    async def test_recovery_runs_kr_job_on_missed(
        self, recovery_manager, mock_kr_repo, mock_us_repo, capfd
    ):
        """Single missed KR execution → recovery runs KR job only."""
        with freeze_time("2024-01-10"):
            yesterday = date(2024, 1, 9)
            
            # Mock missed KR execution
            missed_log = AnalysisLog(
                id=uuid4(),
                date=yesterday,
                market="KR",
                executed=False,
                ai_response=None,
                error_message="System was down"
            )

            # Configure mocks
            mock_kr_repo.get_unexecuted.side_effect = lambda market, check_date: (
                [missed_log] if check_date == yesterday else []
            )
            mock_us_repo.get_unexecuted.return_value = []

            # Mock the recovery job call
            recovery_manager._run_recovery_job = AsyncMock()

            results = await recovery_manager.check_and_recover()

            # Verify KR recovery was triggered
            assert results["kr"]["recovered"] is True
            assert results["kr"]["date"] == yesterday
            assert results["kr"]["error"] is None
            
            # Verify US had no recovery
            assert results["us"]["recovered"] is False

            # Verify recovery job was called with correct parameters
            recovery_manager._run_recovery_job.assert_called_once_with(
                market="KR",
                target_date=yesterday,
                skip_ai=False,  # No cached ai_response
            )

            # Check console output
            captured = capfd.readouterr()
            assert f"[Recovery] KR: found missed execution for {yesterday}" in captured.out
            assert f"[Recovery] KR: recovery successful for {yesterday}" in captured.out

    @pytest.mark.asyncio
    async def test_recovery_uses_most_recent_if_multiple_missed(
        self, recovery_manager, mock_kr_repo, mock_us_repo, capfd
    ):
        """Multiple missed executions → run most recent only."""
        with freeze_time("2024-01-10"):
            older_date = date(2024, 1, 8)
            recent_date = date(2024, 1, 9)
            
            older_log = AnalysisLog(
                id=uuid4(),
                date=older_date,
                market="KR",
                executed=False,
            )
            
            recent_log = AnalysisLog(
                id=uuid4(),
                date=recent_date,
                market="KR",
                executed=False,
            )

            # Return logs for their respective dates
            mock_kr_repo.get_unexecuted.side_effect = lambda market, check_date: (
                [older_log] if check_date == older_date 
                else [recent_log] if check_date == recent_date 
                else []
            )
            mock_us_repo.get_unexecuted.return_value = []

            # Mock the recovery job call
            recovery_manager._run_recovery_job = AsyncMock()

            results = await recovery_manager.check_and_recover()

            # Should recover most recent date only
            assert results["kr"]["recovered"] is True
            assert results["kr"]["date"] == recent_date

            # Verify recovery job was called for recent date only
            recovery_manager._run_recovery_job.assert_called_once_with(
                market="KR",
                target_date=recent_date,
                skip_ai=False,
            )

            # Check console output mentions multiple missed executions
            captured = capfd.readouterr()
            assert "found 2 missed executions" in captured.out
            assert "recovering most recent" in captured.out

    # ── SCENARIO 3: Staleness cutoff ──

    @pytest.mark.asyncio
    async def test_recovery_skips_stale_execution(
        self, recovery_manager, mock_kr_repo, mock_us_repo, capfd
    ):
        """Logs older than MAX_RECOVERY_DAYS must be skipped."""
        with freeze_time("2024-01-10"):
            stale_date = date(2024, 1, 6)  # 4 days ago > MAX(3)
            
            stale_log = AnalysisLog(
                id=uuid4(),
                date=stale_date,
                market="KR",
                executed=False,
            )

            mock_kr_repo.get_unexecuted.side_effect = lambda market, check_date: (
                [stale_log] if check_date == stale_date else []
            )
            mock_us_repo.get_unexecuted.return_value = []

            # Mock the recovery job call
            recovery_manager._run_recovery_job = AsyncMock()

            results = await recovery_manager.check_and_recover()

            # Should NOT attempt recovery (stale)
            assert results["kr"]["recovered"] is False
            assert results["kr"]["date"] == stale_date
            assert results["kr"]["error"] == "stale"

            # Verify recovery job was NOT called
            recovery_manager._run_recovery_job.assert_not_called()

            # Check console output mentions skipping stale
            captured = capfd.readouterr()
            assert "[Recovery] KR: skipping stale execution" in captured.out
            assert "older than 3 days" in captured.out

    @pytest.mark.asyncio
    async def test_recovery_runs_at_boundary_day(
        self, recovery_manager, mock_kr_repo, mock_us_repo
    ):
        """Logs exactly at boundary (3 days ago) should be processed."""
        with freeze_time("2024-01-10"):
            boundary_date = date(2024, 1, 7)  # exactly 3 days ago = within limit
            
            boundary_log = AnalysisLog(
                id=uuid4(),
                date=boundary_date,
                market="KR",
                executed=False,
            )

            mock_kr_repo.get_unexecuted.side_effect = lambda market, check_date: (
                [boundary_log] if check_date == boundary_date else []
            )
            mock_us_repo.get_unexecuted.return_value = []

            # Mock the recovery job call
            recovery_manager._run_recovery_job = AsyncMock()

            results = await recovery_manager.check_and_recover()

            # Should attempt recovery (within boundary)
            assert results["kr"]["recovered"] is True
            assert results["kr"]["date"] == boundary_date
            assert results["kr"]["error"] is None

            # Verify recovery job WAS called
            recovery_manager._run_recovery_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_recovery_skips_at_boundary_plus_one(
        self, recovery_manager, mock_kr_repo, mock_us_repo
    ):
        """Logs beyond boundary (4+ days ago) should be skipped."""
        with freeze_time("2024-01-10"):
            stale_date = date(2024, 1, 6)  # 4 days ago = stale
            
            stale_log = AnalysisLog(
                id=uuid4(),
                date=stale_date,
                market="KR",
                executed=False,
            )

            mock_kr_repo.get_unexecuted.side_effect = lambda market, check_date: (
                [stale_log] if check_date == stale_date else []
            )
            mock_us_repo.get_unexecuted.return_value = []

            # Mock the recovery job call
            recovery_manager._run_recovery_job = AsyncMock()

            results = await recovery_manager.check_and_recover()

            # Should NOT attempt recovery (stale)
            assert results["kr"]["recovered"] is False
            assert results["kr"]["error"] == "stale"

            # Verify recovery job was NOT called
            recovery_manager._run_recovery_job.assert_not_called()

    # ── SCENARIO 4: Partial execution recovery ──

    @pytest.mark.asyncio
    async def test_recovery_skips_ai_when_response_cached(
        self, recovery_manager, mock_kr_repo, mock_us_repo
    ):
        """AI response cached → skip AI call in recovery."""
        with freeze_time("2024-01-10"):
            yesterday = date(2024, 1, 9)
            
            # Mock log with cached AI response
            cached_log = AnalysisLog(
                id=uuid4(),
                date=yesterday,
                market="KR",
                executed=False,
                ai_response={"analysis": "Cached analysis result"},  # AI succeeded
            )

            mock_kr_repo.get_unexecuted.side_effect = lambda market, check_date: (
                [cached_log] if check_date == yesterday else []
            )
            mock_us_repo.get_unexecuted.return_value = []

            # Mock the recovery job call
            recovery_manager._run_recovery_job = AsyncMock()

            await recovery_manager.check_and_recover()

            # Verify recovery job called with skip_ai=True
            recovery_manager._run_recovery_job.assert_called_once_with(
                market="KR",
                target_date=yesterday,
                skip_ai=True,  # Should skip AI due to cached response
            )

    @pytest.mark.asyncio
    async def test_recovery_runs_full_pipeline_when_no_cache(
        self, recovery_manager, mock_kr_repo, mock_us_repo
    ):
        """No cached AI response → run full pipeline."""
        with freeze_time("2024-01-10"):
            yesterday = date(2024, 1, 9)
            
            # Mock log with NO cached AI response
            uncached_log = AnalysisLog(
                id=uuid4(),
                date=yesterday,
                market="KR",
                executed=False,
                ai_response=None,  # No AI response
            )

            mock_kr_repo.get_unexecuted.side_effect = lambda market, check_date: (
                [uncached_log] if check_date == yesterday else []
            )
            mock_us_repo.get_unexecuted.return_value = []

            # Mock the recovery job call
            recovery_manager._run_recovery_job = AsyncMock()

            await recovery_manager.check_and_recover()

            # Verify recovery job called with skip_ai=False
            recovery_manager._run_recovery_job.assert_called_once_with(
                market="KR",
                target_date=yesterday,
                skip_ai=False,  # Should run full pipeline
            )

    # ── SCENARIO 5: Market isolation ──

    @pytest.mark.asyncio
    async def test_kr_recovery_failure_does_not_stop_us_recovery(
        self, recovery_manager, mock_kr_repo, mock_us_repo, capfd
    ):
        """KR recovery failure → US recovery still attempted."""
        with freeze_time("2024-01-10"):
            missed_date = date(2024, 1, 9)
            
            # Both markets have missed executions
            kr_log = AnalysisLog(
                id=uuid4(),
                date=missed_date,
                market="KR",
                executed=False,
            )
            us_log = AnalysisLog(
                id=uuid4(),
                date=missed_date,
                market="US",
                executed=False,
            )

            mock_kr_repo.get_unexecuted.side_effect = lambda market, check_date: (
                [kr_log] if check_date == missed_date else []
            )
            mock_us_repo.get_unexecuted.side_effect = lambda market, check_date: (
                [us_log] if check_date == missed_date else []
            )

            # Mock KR recovery to fail, US recovery to succeed
            async def mock_run_recovery_job(market, target_date, skip_ai):
                if market == "KR":
                    raise RuntimeError("KR recovery failed")
                # US succeeds (no exception)

            recovery_manager._run_recovery_job = AsyncMock(side_effect=mock_run_recovery_job)

            results = await recovery_manager.check_and_recover()

            # KR should have failed
            assert results["kr"]["recovered"] is False
            assert results["kr"]["error"] == "KR recovery failed"

            # US should still have succeeded
            assert results["us"]["recovered"] is True
            assert results["us"]["date"] == missed_date
            assert results["us"]["error"] is None

            # Both recovery attempts should have been made
            assert recovery_manager._run_recovery_job.call_count == 2

            # Check console output shows both attempts
            captured = capfd.readouterr()
            assert "[Recovery] KR: recovery FAILED" in captured.out
            assert "[Recovery] US: recovery successful" in captured.out

    @pytest.mark.asyncio
    async def test_us_recovery_failure_does_not_affect_kr(
        self, recovery_manager, mock_kr_repo, mock_us_repo, capfd
    ):
        """US recovery failure → KR recovery still succeeds."""
        with freeze_time("2024-01-10"):
            missed_date = date(2024, 1, 9)
            
            # Both markets have missed executions
            kr_log = AnalysisLog(
                id=uuid4(),
                date=missed_date,
                market="KR",
                executed=False,
            )
            us_log = AnalysisLog(
                id=uuid4(),
                date=missed_date,
                market="US",
                executed=False,
            )

            mock_kr_repo.get_unexecuted.side_effect = lambda market, check_date: (
                [kr_log] if check_date == missed_date else []
            )
            mock_us_repo.get_unexecuted.side_effect = lambda market, check_date: (
                [us_log] if check_date == missed_date else []
            )

            # Mock US recovery to fail, KR recovery to succeed
            async def mock_run_recovery_job(market, target_date, skip_ai):
                if market == "US":
                    raise RuntimeError("US recovery failed")
                # KR succeeds (no exception)

            recovery_manager._run_recovery_job = AsyncMock(side_effect=mock_run_recovery_job)

            results = await recovery_manager.check_and_recover()

            # KR should have succeeded
            assert results["kr"]["recovered"] is True
            assert results["kr"]["date"] == missed_date
            assert results["kr"]["error"] is None

            # US should have failed
            assert results["us"]["recovered"] is False
            assert results["us"]["error"] == "US recovery failed"

            # Both recovery attempts should have been made
            assert recovery_manager._run_recovery_job.call_count == 2

    # ── SCENARIO 6: US market date handling ──

    @pytest.mark.asyncio
    async def test_us_recovery_uses_log_date_not_yesterday(
        self, recovery_manager, mock_kr_repo, mock_us_repo
    ):
        """US recovery uses exact log date, not yesterday calculation."""
        with freeze_time("2024-01-10"):
            specific_date = date(2024, 1, 2)  # Not yesterday
            
            # Mock US missed execution with specific date
            us_log = AnalysisLog(
                id=uuid4(),
                date=specific_date,
                market="US",
                executed=False,
            )

            mock_kr_repo.get_unexecuted.return_value = []
            mock_us_repo.get_unexecuted.side_effect = lambda market, check_date: (
                [us_log] if check_date == specific_date else []
            )

            # Mock the recovery job call
            recovery_manager._run_recovery_job = AsyncMock()

            await recovery_manager.check_and_recover()

            # Verify recovery job called with exact log date
            recovery_manager._run_recovery_job.assert_called_once_with(
                market="US",
                target_date=specific_date,  # Should use log's date, not yesterday
                skip_ai=False,
            )

    # ── SCENARIO 7: Both markets missed ──

    @pytest.mark.asyncio
    async def test_both_markets_recovered_independently(
        self, recovery_manager, mock_kr_repo, mock_us_repo
    ):
        """Both markets missed → both get recovered independently."""
        with freeze_time("2024-01-10"):
            kr_date = date(2024, 1, 9)
            us_date = date(2024, 1, 8)  # Different dates
            
            kr_log = AnalysisLog(
                id=uuid4(),
                date=kr_date,
                market="KR",
                executed=False,
            )
            us_log = AnalysisLog(
                id=uuid4(),
                date=us_date,
                market="US",
                executed=False,
            )

            mock_kr_repo.get_unexecuted.side_effect = lambda market, check_date: (
                [kr_log] if check_date == kr_date else []
            )
            mock_us_repo.get_unexecuted.side_effect = lambda market, check_date: (
                [us_log] if check_date == us_date else []
            )

            # Mock the recovery job call
            recovery_manager._run_recovery_job = AsyncMock()

            results = await recovery_manager.check_and_recover()

            # Both should be recovered
            assert results["kr"]["recovered"] is True
            assert results["kr"]["date"] == kr_date
            assert results["us"]["recovered"] is True
            assert results["us"]["date"] == us_date

            # Both recovery jobs should be called
            assert recovery_manager._run_recovery_job.call_count == 2
            
            # Verify specific calls
            expected_calls = [
                ("KR", kr_date, False),
                ("US", us_date, False),
            ]
            actual_calls = [
                (call.kwargs["market"], call.kwargs["target_date"], call.kwargs["skip_ai"])
                for call in recovery_manager._run_recovery_job.call_args_list
            ]
            assert set(actual_calls) == set(expected_calls)