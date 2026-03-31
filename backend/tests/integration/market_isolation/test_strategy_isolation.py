import pytest
from datetime import date
from decimal import Decimal


@pytest.mark.integration
async def test_kr_strategy_has_kr_market_field(db_session):
    """
    Strategies generated for KR market must have market="KR".
    """
    from app.infra.db.repositories.strategy_output_repository import StrategyOutputRepository
    from app.infra.db.repositories.analysis_log_repository import AnalysisLogRepository
    from app.domain.strategy.schemas import UnifiedStrategy

    log_repo = AnalysisLogRepository(db_session)
    strategy_repo = StrategyOutputRepository(db_session)
    today = date.today()

    # Create KR analysis log
    kr_log = await log_repo.save(date=today, market="KR", executed=True)

    # Create KR strategy
    kr_strategy = UnifiedStrategy(
        ticker="005930",
        market="KR",
        final_action="hold",
        action_source="ai",
        confidence=Decimal("0.8"),
        rationale="KR 테스트 전략",
        sell_quantity=Decimal("0"),
        realized_pnl_estimate=Decimal("0"),
        changed_from_last=True,
    )

    await strategy_repo.save(kr_log.id, kr_strategy)

    # Verify market field
    strategies = await strategy_repo.get_by_analysis_log(kr_log.id)
    assert len(strategies) == 1
    # Verify ticker is KR format (6-digit)
    assert strategies[0].ticker == "005930"
    assert strategies[0].ticker.isdigit()


@pytest.mark.integration
async def test_kr_and_us_strategies_stored_separately(db_session):
    """
    KR and US strategies linked to different analysis_logs.
    get_by_analysis_log must not mix markets.
    """
    from app.infra.db.repositories.strategy_output_repository import StrategyOutputRepository
    from app.infra.db.repositories.analysis_log_repository import AnalysisLogRepository
    from app.domain.strategy.schemas import UnifiedStrategy

    log_repo = AnalysisLogRepository(db_session)
    strategy_repo = StrategyOutputRepository(db_session)
    today = date.today()

    kr_log = await log_repo.save(date=today, market="KR", executed=True)
    us_log = await log_repo.save(date=today, market="US", executed=True)

    kr_strat = UnifiedStrategy(
        ticker="005930", market="KR",
        final_action="buy", action_source="ai",
        confidence=Decimal("0.8"),
        rationale="KR 전략",
        sell_quantity=Decimal("0"),
        realized_pnl_estimate=Decimal("0"),
        changed_from_last=True,
    )
    us_strat = UnifiedStrategy(
        ticker="AAPL", market="US",
        final_action="hold", action_source="ai",
        confidence=Decimal("0.7"),
        rationale="US strategy",
        sell_quantity=Decimal("0"),
        realized_pnl_estimate=Decimal("0"),
        changed_from_last=True,
    )

    await strategy_repo.save(kr_log.id, kr_strat)
    await strategy_repo.save(us_log.id, us_strat)

    # Fetch by analysis_log — must not mix
    kr_strategies = await strategy_repo.get_by_analysis_log(kr_log.id)
    us_strategies = await strategy_repo.get_by_analysis_log(us_log.id)

    assert len(kr_strategies) == 1
    assert len(us_strategies) == 1
    assert kr_strategies[0].ticker == "005930"
    assert us_strategies[0].ticker == "AAPL"

    # Verify no cross-contamination
    kr_tickers = {s.ticker for s in kr_strategies}
    us_tickers = {s.ticker for s in us_strategies}
    assert len(kr_tickers & us_tickers) == 0  # empty set