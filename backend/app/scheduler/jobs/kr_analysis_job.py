"""
KR Market Daily Analysis Job.
Runs KR stock analysis after KOSPI market close.
"""

from datetime import date, datetime

import pytz

from app.core.config import get_settings
from app.core.container import get_container
from app.infra.db.base import AsyncSessionLocal

KST = pytz.timezone("Asia/Seoul")


async def run_kr_analysis(
    date_override: date | None = None,
    skip_ai_if_cached: bool = False,
) -> None:
    """
    Run KR market daily analysis job.
    
    Args:
        date_override: if set, use this date instead of today (KST).
        skip_ai_if_cached: if True, skip AI call (use cached ai_response from DB).
    
    Flow:
    1. Check if already executed today (idempotency)
    2. Fetch market data for all KR tickers
    3. Run indicator calculations  
    4. Apply filtering chains
    5. Run AI analysis pipeline
    6. Run strategy integration
    7. Mark as executed (handled by pipeline)
    """
    settings = get_settings()
    if not settings.kr_tickers:
        print("⚠️  No KR tickers configured")
        return

    # Use date_override if provided, otherwise current KST date for KR market
    if date_override:
        analysis_date = date_override
    else:
        KST = pytz.timezone("Asia/Seoul")
        kst_now = datetime.now(KST)
        analysis_date = kst_now.date()

    async with AsyncSessionLocal() as session:
        container = get_container()
        analysis_log_repo = container.analysis_log_repository(session)

        # Check if already executed today
        if await analysis_log_repo.exists("KR", analysis_date):
            print(f"✅ KR analysis already executed for {analysis_date}")
            return

        try:
            print(f"🇰🇷 Starting KR analysis for {analysis_date}")

            # Fetch market data for all tickers
            market_service = container.market_data_service(session)
            market_data = []

            for ticker in settings.kr_tickers:
                data = await market_service.fetch_and_cache(ticker, "KR", analysis_date)
                if data:
                    data["ticker"] = ticker
                    market_data.append(data)

            if not market_data:
                error_msg = "No market data available"
                print(f"❌ {error_msg}")
                await analysis_log_repo.save(
                    date=analysis_date,
                    market="KR",
                    executed=False,
                    error_message=error_msg
                )
                return

            # Run indicator calculations
            indicator_engine = container.indicator_engine(session)
            for data_point in market_data:
                await indicator_engine.calculate_indicators(
                    data_point["ticker"], "KR", analysis_date
                )

            # Apply filtering chains
            filter_chain = container.filter_chain(session)
            filtered_data = await filter_chain.apply(market_data)

            # Run AI analysis pipeline
            ai_pipeline = container.analysis_pipeline(session)
            ai_result = await ai_pipeline.run(filtered_data, "KR", analysis_date)

            # Run strategy integration
            strategy_engine = container.strategy_integration_engine(session)
            strategy_result = await strategy_engine.run(ai_result, "KR", analysis_date)

            print(
                f"✅ KR analysis completed: "
                f"{strategy_result.total_tickers_analyzed} tickers analyzed"
            )

        except Exception as e:
            print(f"❌ KR analysis failed: {str(e)}")
            await analysis_log_repo.save(
                date=analysis_date,
                market="KR",
                executed=False,
                error_message=str(e)
            )
            raise
