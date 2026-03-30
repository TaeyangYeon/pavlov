"""
Integration tests for RecoveryManager.
Tests full integration with database and actual log repository operations.
"""

from datetime import date, timedelta

import pytest
from freezegun import freeze_time

from app.core.container import get_container
from app.infra.db.repositories.analysis_log_repository import AnalysisLogRepository
from app.scheduler.recovery import RecoveryManager


@pytest.mark.integration
class TestRecoveryIntegration:
    """Integration tests for RecoveryManager with real database."""

    @pytest.fixture
    async def kr_repo(self, db_session):
        """KR analysis log repository."""
        return AnalysisLogRepository(db_session)

    @pytest.fixture
    async def us_repo(self, db_session):
        """US analysis log repository."""
        return AnalysisLogRepository(db_session)

    @pytest.fixture
    async def recovery_manager(self, kr_repo, us_repo):
        """Recovery manager with real repositories."""
        return RecoveryManager(kr_repo, us_repo)

    async def test_recovery_detects_missed_kr_execution(
        self, recovery_manager, kr_repo, db_session
    ):
        """
        Full integration: insert unexecuted log → verify recovery
        detects it and attempts recovery job.
        """
        with freeze_time("2024-01-10"):
            yesterday = date(2024, 1, 9)

            # Insert missed execution log (yesterday, not executed)
            await kr_repo.save(
                date=yesterday,
                market="KR",
                executed=False,
                error_message="Simulated missed execution"
            )

            # Verify get_unexecuted finds it
            missed = await kr_repo.get_unexecuted("KR", yesterday)
            assert len(missed) == 1
            assert missed[0].executed is False
            assert missed[0].date == yesterday

            print(f"[Test] Verified: 1 missed KR execution found for {yesterday}")

            # Mock the actual job execution to avoid running the full pipeline
            original_run_recovery_job = recovery_manager._run_recovery_job
            recovery_calls = []

            async def mock_run_recovery_job(market, target_date, skip_ai):
                recovery_calls.append((market, target_date, skip_ai))
                # Don't actually run the job, just record the call
                return

            recovery_manager._run_recovery_job = mock_run_recovery_job

            # Run recovery and verify it detects the missed execution
            results = await recovery_manager.check_and_recover()

            # Should attempt KR recovery
            assert results["kr"]["recovered"] is True
            assert results["kr"]["date"] == yesterday
            assert results["kr"]["error"] is None

            # Should not attempt US recovery (no missed execution)
            assert results["us"]["recovered"] is False
            assert results["us"]["date"] is None
            assert results["us"]["error"] is None

            # Verify the recovery job was called with correct parameters
            assert len(recovery_calls) == 1
            market, target_date, skip_ai = recovery_calls[0]
            assert market == "KR"
            assert target_date == yesterday
            assert skip_ai is False  # No cached ai_response

            # Restore original method
            recovery_manager._run_recovery_job = original_run_recovery_job

    async def test_recovery_skips_already_executed(
        self, recovery_manager, us_repo, db_session
    ):
        """
        Executed logs must not appear in recovery candidates.
        """
        with freeze_time("2024-01-10"):
            yesterday = date(2024, 1, 9)

            # Insert EXECUTED log
            saved_log = await us_repo.save(
                date=yesterday,
                market="US",
                executed=False,  # Initially not executed
            )

            # Mark it as executed
            await us_repo.mark_executed(saved_log.id)

            # Should not find any unexecuted after marking executed
            missed = await us_repo.get_unexecuted("US", yesterday)
            assert len(missed) == 0

            # Recovery should not attempt any recovery
            results = await recovery_manager.check_and_recover()
            assert results["us"]["recovered"] is False
            assert results["us"]["date"] is None
            assert results["us"]["error"] is None

    async def test_staleness_cutoff_in_recovery(
        self, recovery_manager, kr_repo, db_session
    ):
        """
        Logs older than MAX_RECOVERY_DAYS must be skipped.
        """
        with freeze_time("2024-01-10"):
            # Insert log 5 days ago (beyond default cutoff of 3)
            stale_date = date(2024, 1, 5)  # 5 days ago > MAX(3)
            await kr_repo.save(
                date=stale_date,
                market="KR",
                executed=False,
                error_message="Old missed execution"
            )

            # Verify the log exists in database
            missed = await kr_repo.get_unexecuted("KR", stale_date)
            assert len(missed) == 1
            assert missed[0].date == stale_date

            # Recovery should skip it due to staleness
            results = await recovery_manager.check_and_recover()

            # Should NOT attempt recovery (stale)
            assert results["kr"]["recovered"] is False
            assert results["kr"]["date"] == stale_date
            assert results["kr"]["error"] == "stale"

    async def test_recovery_at_boundary_day(
        self, recovery_manager, kr_repo, db_session
    ):
        """
        Logs exactly at boundary (3 days ago) should be processed.
        """
        with freeze_time("2024-01-10"):
            # Insert log exactly 3 days ago (within boundary)
            boundary_date = date(2024, 1, 7)  # exactly 3 days ago = within limit
            await kr_repo.save(
                date=boundary_date,
                market="KR",
                executed=False,
                error_message="Boundary missed execution"
            )

            # Mock the recovery job to avoid actual execution
            recovery_calls = []

            async def mock_run_recovery_job(market, target_date, skip_ai):
                recovery_calls.append((market, target_date, skip_ai))
                return

            recovery_manager._run_recovery_job = mock_run_recovery_job

            # Recovery should attempt it (within boundary)
            results = await recovery_manager.check_and_recover()

            # Should attempt recovery (within boundary)
            assert results["kr"]["recovered"] is True
            assert results["kr"]["date"] == boundary_date
            assert results["kr"]["error"] is None

            # Verify recovery job was called
            assert len(recovery_calls) == 1
            market, target_date, skip_ai = recovery_calls[0]
            assert market == "KR"
            assert target_date == boundary_date

    async def test_partial_execution_recovery_with_cached_response(
        self, recovery_manager, kr_repo, db_session
    ):
        """
        Test recovery behavior when AI response is cached.
        """
        with freeze_time("2024-01-10"):
            yesterday = date(2024, 1, 9)

            # Insert log with cached AI response (partial execution)
            await kr_repo.save(
                date=yesterday,
                market="KR",
                executed=False,
                ai_response={"analysis": "Cached analysis result", "confidence": 0.85},
                error_message="Strategy engine failed"
            )

            # Mock the recovery job to capture parameters
            recovery_calls = []

            async def mock_run_recovery_job(market, target_date, skip_ai):
                recovery_calls.append((market, target_date, skip_ai))
                return

            recovery_manager._run_recovery_job = mock_run_recovery_job

            # Run recovery
            results = await recovery_manager.check_and_recover()

            # Should attempt recovery
            assert results["kr"]["recovered"] is True
            assert results["kr"]["date"] == yesterday
            assert results["kr"]["error"] is None

            # Verify recovery job was called with skip_ai=True
            assert len(recovery_calls) == 1
            market, target_date, skip_ai = recovery_calls[0]
            assert market == "KR"
            assert target_date == yesterday
            assert skip_ai is True  # Should skip AI due to cached response

    async def test_multiple_missed_executions_recovery_most_recent(
        self, recovery_manager, us_repo, db_session
    ):
        """
        Test that recovery chooses most recent when multiple missed executions exist.
        """
        with freeze_time("2024-01-10"):
            # Insert multiple missed executions
            older_date = date(2024, 1, 7)  # 3 days ago
            recent_date = date(2024, 1, 9)  # 1 day ago

            await us_repo.save(
                date=older_date,
                market="US",
                executed=False,
                error_message="Older missed execution"
            )

            await us_repo.save(
                date=recent_date,
                market="US",
                executed=False,
                error_message="Recent missed execution"
            )

            # Verify both logs exist
            older_missed = await us_repo.get_unexecuted("US", older_date)
            recent_missed = await us_repo.get_unexecuted("US", recent_date)
            assert len(older_missed) == 1
            assert len(recent_missed) == 1

            # Mock the recovery job
            recovery_calls = []

            async def mock_run_recovery_job(market, target_date, skip_ai):
                recovery_calls.append((market, target_date, skip_ai))
                return

            recovery_manager._run_recovery_job = mock_run_recovery_job

            # Run recovery
            results = await recovery_manager.check_and_recover()

            # Should recover the most recent date only
            assert results["us"]["recovered"] is True
            assert results["us"]["date"] == recent_date  # Most recent
            assert results["us"]["error"] is None

            # Verify only one recovery job was called for the most recent date
            assert len(recovery_calls) == 1
            market, target_date, skip_ai = recovery_calls[0]
            assert market == "US"
            assert target_date == recent_date  # Should use most recent, not older

    async def test_both_markets_recovery_independence(
        self, recovery_manager, kr_repo, us_repo, db_session
    ):
        """
        Test that both markets can be recovered independently.
        """
        with freeze_time("2024-01-10"):
            kr_date = date(2024, 1, 9)
            us_date = date(2024, 1, 8)

            # Insert missed executions for both markets
            await kr_repo.save(
                date=kr_date,
                market="KR",
                executed=False,
                error_message="KR missed execution"
            )

            await us_repo.save(
                date=us_date,
                market="US",
                executed=False,
                error_message="US missed execution"
            )

            # Mock the recovery job
            recovery_calls = []

            async def mock_run_recovery_job(market, target_date, skip_ai):
                recovery_calls.append((market, target_date, skip_ai))
                return

            recovery_manager._run_recovery_job = mock_run_recovery_job

            # Run recovery
            results = await recovery_manager.check_and_recover()

            # Both markets should be recovered
            assert results["kr"]["recovered"] is True
            assert results["kr"]["date"] == kr_date
            assert results["kr"]["error"] is None

            assert results["us"]["recovered"] is True
            assert results["us"]["date"] == us_date
            assert results["us"]["error"] is None

            # Both recovery jobs should be called
            assert len(recovery_calls) == 2

            # Verify specific calls (order may vary)
            recovery_dict = {call[0]: (call[1], call[2]) for call in recovery_calls}
            assert "KR" in recovery_dict
            assert "US" in recovery_dict
            assert recovery_dict["KR"] == (kr_date, False)  # No cached AI response
            assert recovery_dict["US"] == (us_date, False)  # No cached AI response

    async def test_no_missed_executions_scenario(
        self, recovery_manager, kr_repo, us_repo, db_session
    ):
        """
        Test recovery behavior when no missed executions exist.
        """
        with freeze_time("2024-01-10"):
            # Don't insert any missed executions

            # Mock the recovery job to ensure it's not called
            recovery_calls = []

            async def mock_run_recovery_job(market, target_date, skip_ai):
                recovery_calls.append((market, target_date, skip_ai))
                return

            recovery_manager._run_recovery_job = mock_run_recovery_job

            # Run recovery
            results = await recovery_manager.check_and_recover()

            # No recovery should be attempted
            assert results["kr"]["recovered"] is False
            assert results["kr"]["date"] is None
            assert results["kr"]["error"] is None

            assert results["us"]["recovered"] is False
            assert results["us"]["date"] is None
            assert results["us"]["error"] is None

            # No recovery jobs should be called
            assert len(recovery_calls) == 0