import pytest
import asyncio
from datetime import date, timedelta


@pytest.mark.integration
async def test_kr_full_analysis_flow(db_session):
    """
    Complete KR flow:
    mock data → indicator → filter → AI → strategy → log
    Verifies all components connect correctly for KR.
    """
    from app.domain.ai.client import MockAIClient
    from app.domain.ai.pipeline import AnalysisPipeline
    from app.domain.ai.schemas import AIPromptInput
    from app.infra.db.repositories.analysis_log_repository import AnalysisLogRepository

    log_repo = AnalysisLogRepository(db_session)
    mock_client = MockAIClient()
    pipeline = AnalysisPipeline(mock_client, log_repo)

    prompt_input = AIPromptInput(
        market="KR",
        date=date.today().isoformat(),
        filtered_stocks=[],
        held_positions=[],
    )

    result = await pipeline.run(prompt_input, date.today())

    # Verify log written with correct market
    kr_exists = await log_repo.exists("KR", date.today())
    us_exists = await log_repo.exists("US", date.today())

    assert kr_exists is True
    assert us_exists is False   # US not touched


@pytest.mark.integration
async def test_us_full_analysis_flow(db_session):
    """Same as above for US market."""
    from app.domain.ai.client import MockAIClient
    from app.domain.ai.pipeline import AnalysisPipeline
    from app.domain.ai.schemas import AIPromptInput
    from app.infra.db.repositories.analysis_log_repository import AnalysisLogRepository

    log_repo = AnalysisLogRepository(db_session)
    mock_client = MockAIClient()
    pipeline = AnalysisPipeline(mock_client, log_repo)

    yesterday = date.today() - timedelta(days=1)
    prompt_input = AIPromptInput(
        market="US",
        date=yesterday.isoformat(),
        filtered_stocks=[],
        held_positions=[],
    )

    await pipeline.run(prompt_input, yesterday)

    kr_exists = await log_repo.exists("KR", yesterday)
    us_exists = await log_repo.exists("US", yesterday)

    assert kr_exists is False   # KR not touched
    assert us_exists is True


@pytest.mark.integration
async def test_concurrent_kr_us_no_interference(db_session):
    """
    KR and US run concurrently → no data interference.
    """
    from app.domain.ai.client import MockAIClient
    from app.domain.ai.pipeline import AnalysisPipeline
    from app.domain.ai.schemas import AIPromptInput
    from app.infra.db.repositories.analysis_log_repository import AnalysisLogRepository

    today = date.today()
    yesterday = today - timedelta(days=1)

    # Use separate sessions for concurrent simulation
    log_repo = AnalysisLogRepository(db_session)
    kr_client = MockAIClient()
    us_client = MockAIClient()
    kr_pipeline = AnalysisPipeline(kr_client, log_repo)
    us_pipeline = AnalysisPipeline(us_client, log_repo)

    kr_input = AIPromptInput(
        market="KR", date=today.isoformat(),
        filtered_stocks=[], held_positions=[]
    )
    us_input = AIPromptInput(
        market="US", date=yesterday.isoformat(),
        filtered_stocks=[], held_positions=[]
    )

    # Run both pipelines
    await asyncio.gather(
        kr_pipeline.run(kr_input, today),
        us_pipeline.run(us_input, yesterday),
    )

    # Verify each market's log is correct
    kr_today = await log_repo.exists("KR", today)
    us_yesterday = await log_repo.exists("US", yesterday)
    kr_yesterday = await log_repo.exists("KR", yesterday)
    us_today = await log_repo.exists("US", today)

    assert kr_today is True
    assert us_yesterday is True
    assert kr_yesterday is False   # No cross-contamination
    assert us_today is False       # No cross-contamination