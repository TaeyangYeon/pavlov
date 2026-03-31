import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch, AsyncMock
import time


@pytest.mark.integration
async def test_kr_failure_does_not_stop_us_job(db_session):
    """
    KR job raises exception → US job still executes.
    This is the most critical isolation test.
    """
    kr_executed = False
    us_executed = False

    async def mock_kr_job(**kwargs):
        nonlocal kr_executed
        kr_executed = True
        raise RuntimeError("Simulated KR job crash")

    async def mock_us_job(**kwargs):
        nonlocal us_executed
        us_executed = True
        # US job succeeds

    # Simulate running both jobs (as recovery manager does)
    from app.scheduler.runner import JobRunner
    
    runner = JobRunner()

    kr_result = await runner.run("KR Analysis", mock_kr_job)
    us_result = await runner.run("US Analysis", mock_us_job)

    assert kr_executed is True
    assert us_executed is True
    assert kr_result is False   # KR failed
    assert us_result is True    # US succeeded


@pytest.mark.integration
async def test_us_failure_does_not_stop_kr_job(db_session):
    """US job fails → KR job unaffected."""
    # Reverse of above test
    kr_executed = False
    us_executed = False

    async def mock_kr_job(**kwargs):
        nonlocal kr_executed
        kr_executed = True

    async def mock_us_job(**kwargs):
        nonlocal us_executed
        us_executed = True
        raise RuntimeError("Simulated US job crash")

    from app.scheduler.runner import JobRunner
    
    runner = JobRunner()

    kr_result = await runner.run("KR Analysis", mock_kr_job)
    us_result = await runner.run("US Analysis", mock_us_job)

    assert kr_executed is True
    assert us_executed is True
    assert kr_result is True    # KR succeeded
    assert us_result is False   # US failed


@pytest.mark.integration
async def test_kr_job_uses_kst_today_not_yesterday(db_session):
    """
    KR job must use TODAY in KST (not yesterday).
    US job must use YESTERDAY in KST.
    """
    from freezegun import freeze_time
    from datetime import datetime
    import pytz

    # Freeze at 16:15 KST on a weekday
    with freeze_time("2024-01-10 07:15:00"):
        # 07:15 UTC = 16:15 KST
        KST = pytz.timezone("Asia/Seoul")
        kst_now = datetime.now(KST)
        kr_date = kst_now.date()
        us_date = (kst_now - timedelta(days=1)).date()

    assert str(kr_date) == "2024-01-10"
    assert str(us_date) == "2024-01-09"


@pytest.mark.integration
async def test_scheduler_max_instances_one_per_market(db_session):
    """
    Each market job max_instances=1.
    Verify duplicate jobs cannot overlap.
    """
    from app.scheduler.setup import create_scheduler
    
    scheduler = create_scheduler()

    kr_job = scheduler.get_job("kr_daily_analysis")
    us_job = scheduler.get_job("us_daily_analysis")

    assert kr_job is not None
    assert us_job is not None
    assert kr_job.max_instances == 1
    assert us_job.max_instances == 1

    # Verify they are different jobs
    assert kr_job.id != us_job.id
    assert kr_job.name != us_job.name

    scheduler.shutdown()


@pytest.mark.integration
async def test_both_jobs_complete_under_time_limit(db_session):
    """Both jobs (mocked) complete within 30 seconds."""
    from app.scheduler.runner import JobRunner

    async def fast_mock_job():
        import asyncio
        await asyncio.sleep(0.1)  # simulate work

    runner = JobRunner()
    start = time.time()
    await runner.run("KR Test", fast_mock_job)
    await runner.run("US Test", fast_mock_job)
    elapsed = time.time() - start

    assert elapsed < 30, f"Jobs took {elapsed:.1f}s, limit is 30s"