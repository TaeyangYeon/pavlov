"""
US Market Daily Analysis Job.
Runs US stock analysis using previous day's NYSE data.
"""

from datetime import date, datetime, timedelta

import pytz

from app.core.config import get_settings
from app.core.container import get_container
from app.infra.db.base import AsyncSessionLocal

KST = pytz.timezone("Asia/Seoul")


async def run_us_analysis(
    date_override: date | None = None,
    skip_ai_if_cached: bool = False,
) -> None:
    """
    Run US market daily analysis job.
    
    Args:
        date_override: if set, use this date instead of yesterday.
        skip_ai_if_cached: if True, skip AI call (use cached ai_response from DB).
    
    Uses PREVIOUS DAY's date for NYSE data since US job runs at 07:10 KST
    when NYSE hasn't opened yet for current day.
    
    Flow:
    1. Check if already executed for target date (idempotency)
    2. Fetch market data for all US tickers (previous day)
    3. Apply filtering chains
    4. Run AI analysis pipeline
    5. Run strategy integration
    6. Mark as executed (handled by pipeline)
    """
    settings = get_settings()
    if not settings.us_tickers:
        print("⚠️  No US tickers configured")
        return

    # Use date_override if provided, otherwise PREVIOUS DAY for US market data 
    # (07:10 KST is before NYSE open)
    if date_override:
        analysis_date = date_override
    else:
        KST = pytz.timezone("Asia/Seoul")
        kst_now = datetime.now(KST)
        analysis_date = (kst_now - timedelta(days=1)).date()

    async with AsyncSessionLocal() as session:
        container = get_container()
        analysis_log_repo = container.analysis_log_repository(session)

        # Check if already executed for target date
        if await analysis_log_repo.exists("US", analysis_date):
            print(f"✅ US analysis already executed for {analysis_date}")
            return

        try:
            print(f"🇺🇸 Starting US analysis for {analysis_date} (previous day data)")

            # Fetch market data for all tickers
            market_service = container.market_data_service(session)
            market_data = []

            for ticker in settings.us_tickers:
                data = await market_service.fetch_and_cache(ticker, "US", analysis_date)
                if data:
                    data["ticker"] = ticker
                    market_data.append(data)

            # Apply filtering chains (even with empty data)
            filter_chain = container.filter_chain(session)
            filtered_data = await filter_chain.apply(market_data)

            # Run AI analysis pipeline
            ai_pipeline = container.analysis_pipeline(session)
            ai_result = await ai_pipeline.run(filtered_data, "US", analysis_date)

            # Run strategy integration
            strategy_engine = container.strategy_integration_engine(session)
            strategy_result = await strategy_engine.run(ai_result, "US", analysis_date)

            print(
                f"✅ US analysis completed: "
                f"{strategy_result.total_tickers_analyzed} tickers analyzed"
            )

        except Exception as e:
            print(f"❌ US analysis failed: {str(e)}")
            await analysis_log_repo.save(
                date=analysis_date,
                market="US",
                executed=False,
                error_message=str(e)
            )
            raise
