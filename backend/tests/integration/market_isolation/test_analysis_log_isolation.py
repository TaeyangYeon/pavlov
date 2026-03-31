import pytest
from datetime import date, timedelta
from sqlalchemy import select


@pytest.mark.integration
async def test_kr_log_not_visible_in_us_query(db_session):
    """
    KR analysis log must not appear in US queries.
    DB market field must correctly scope queries.
    """
    from app.infra.db.repositories.analysis_log_repository import AnalysisLogRepository
    
    repo = AnalysisLogRepository(db_session)
    today = date.today()

    # Insert KR log
    await repo.save(
        date=today,
        market="KR",
        executed=True,
    )

    # Query US — must not find KR log
    us_unexecuted = await repo.get_unexecuted("US", today)
    assert len(us_unexecuted) == 0

    # Query KR — must find it (executed, so not in unexecuted)
    kr_unexecuted = await repo.get_unexecuted("KR", today)
    assert len(kr_unexecuted) == 0

    # Verify exists() is market-scoped
    kr_exists = await repo.exists("KR", today)
    us_exists = await repo.exists("US", today)
    assert kr_exists is True
    assert us_exists is False


@pytest.mark.integration
async def test_us_executed_does_not_satisfy_kr_check(db_session):
    """
    US analysis executed=True must NOT satisfy KR check.
    This prevents cross-market idempotency confusion.
    """
    from app.infra.db.repositories.analysis_log_repository import AnalysisLogRepository
    
    repo = AnalysisLogRepository(db_session)
    today = date.today()

    # Only US is executed
    await repo.save(
        date=today,
        market="US",
        executed=True,
    )

    # KR should still be "not executed"
    kr_exists = await repo.exists("KR", today)
    us_exists = await repo.exists("US", today)

    assert kr_exists is False   # KR not run
    assert us_exists is True    # US ran


@pytest.mark.integration
async def test_both_markets_can_have_logs_same_date(db_session):
    """
    Same date, both KR and US logs coexist independently.
    """
    from app.infra.db.repositories.analysis_log_repository import AnalysisLogRepository
    
    repo = AnalysisLogRepository(db_session)
    today = date.today()

    await repo.save(date=today, market="KR", executed=True)
    await repo.save(date=today, market="US", executed=False)

    kr_exists = await repo.exists("KR", today)
    us_exists = await repo.exists("US", today)

    assert kr_exists is True
    assert us_exists is False  # US executed=False

    # Verify unexecuted query is market-scoped
    kr_unexecuted = await repo.get_unexecuted("KR", today)
    us_unexecuted = await repo.get_unexecuted("US", today)

    assert len(kr_unexecuted) == 0  # KR executed=True
    assert len(us_unexecuted) == 1  # US executed=False


@pytest.mark.integration
async def test_analysis_log_market_field_stored_correctly(db_session):
    """
    Verify market field in DB matches what was saved.
    No cross-contamination at storage level.
    """
    from app.infra.db.repositories.analysis_log_repository import AnalysisLogRepository
    from app.infra.db.models.analysis_log import AnalysisLog

    repo = AnalysisLogRepository(db_session)
    today = date.today()

    kr_log = await repo.save(
        date=today, market="KR", executed=True
    )
    us_log = await repo.save(
        date=today, market="US", executed=True
    )

    # Verify directly from DB
    kr_check = await db_session.execute(
        select(AnalysisLog).where(AnalysisLog.id == kr_log.id)
    )
    us_check = await db_session.execute(
        select(AnalysisLog).where(AnalysisLog.id == us_log.id)
    )

    kr_row = kr_check.scalar_one()
    us_row = us_check.scalar_one()

    assert str(kr_row.market) in ("KR", "MarketEnum.KR")
    assert str(us_row.market) in ("US", "MarketEnum.US")
    assert kr_row.id != us_row.id