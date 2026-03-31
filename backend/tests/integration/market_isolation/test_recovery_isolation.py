import pytest
from datetime import date, timedelta
from unittest.mock import patch


@pytest.mark.integration
async def test_kr_missed_triggers_only_kr_recovery(db_session):
    """
    KR missed execution → only KR recovery job runs.
    US recovery must NOT be triggered.
    """
    from app.infra.db.repositories.analysis_log_repository import AnalysisLogRepository
    from app.scheduler.recovery import RecoveryManager

    repo = AnalysisLogRepository(db_session)
    yesterday = date.today() - timedelta(days=1)

    # Insert KR missed execution only
    await repo.save(
        date=yesterday,
        market="KR",
        executed=False,
        error_message="Simulated KR miss"
    )
    # US has no missed execution

    kr_recovery_called = False
    us_recovery_called = False

    async def mock_kr_recovery(*args, **kwargs):
        nonlocal kr_recovery_called
        kr_recovery_called = True

    async def mock_us_recovery(*args, **kwargs):
        nonlocal us_recovery_called
        us_recovery_called = True

    recovery = RecoveryManager(repo, repo)

    with patch('app.scheduler.recovery.run_kr_analysis', mock_kr_recovery):
        with patch('app.scheduler.recovery.run_us_analysis', mock_us_recovery):
            results = await recovery.check_and_recover()

    assert kr_recovery_called is True   # KR recovered
    assert us_recovery_called is False  # US untouched
    assert results["kr"]["recovered"] is True
    assert results["us"]["recovered"] is False


@pytest.mark.integration
async def test_us_missed_triggers_only_us_recovery(db_session):
    """
    US missed execution → only US recovery job runs.
    KR recovery must NOT be triggered.
    """
    from app.infra.db.repositories.analysis_log_repository import AnalysisLogRepository
    from app.scheduler.recovery import RecoveryManager

    repo = AnalysisLogRepository(db_session)
    yesterday = date.today() - timedelta(days=1)

    # Only US missed
    await repo.save(
        date=yesterday,
        market="US",
        executed=False,
    )

    kr_recovery_called = False
    us_recovery_called = False

    async def mock_kr(*args, **kwargs):
        nonlocal kr_recovery_called
        kr_recovery_called = True

    async def mock_us(*args, **kwargs):
        nonlocal us_recovery_called
        us_recovery_called = True

    recovery = RecoveryManager(repo, repo)

    with patch('app.scheduler.recovery.run_kr_analysis', mock_kr):
        with patch('app.scheduler.recovery.run_us_analysis', mock_us):
            results = await recovery.check_and_recover()

    assert kr_recovery_called is False  # KR untouched
    assert us_recovery_called is True   # US recovered


@pytest.mark.integration
async def test_kr_recovery_failure_allows_us_recovery(db_session):
    """
    KR recovery fails → US recovery still runs.
    This is the key fault tolerance test.
    """
    from app.infra.db.repositories.analysis_log_repository import AnalysisLogRepository
    from app.scheduler.recovery import RecoveryManager

    repo = AnalysisLogRepository(db_session)
    yesterday = date.today() - timedelta(days=1)

    # Both markets missed
    await repo.save(date=yesterday, market="KR", executed=False)
    await repo.save(date=yesterday, market="US", executed=False)

    us_recovery_called = False

    async def failing_kr(*args, **kwargs):
        raise RuntimeError("KR recovery crashed!")

    async def succeeding_us(*args, **kwargs):
        nonlocal us_recovery_called
        us_recovery_called = True

    recovery = RecoveryManager(repo, repo)

    with patch('app.scheduler.recovery.run_kr_analysis', failing_kr):
        with patch('app.scheduler.recovery.run_us_analysis', succeeding_us):
            results = await recovery.check_and_recover()

    # KR failed but US still ran
    assert us_recovery_called is True
    assert results["kr"]["recovered"] is False
    assert results["kr"]["error"] is not None
    # US either succeeded or at least attempted
    assert results["us"] is not None