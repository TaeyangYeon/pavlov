"""
Cache Pre-warming Jobs for Step 26: Performance Optimization.
Pre-warms market data cache before analysis jobs to achieve >90% hit rate.
"""

import pytz
from datetime import datetime, timedelta


async def run_kr_cache_warmup() -> None:
    """
    Pre-warm KR market data cache at 15:50 KST.
    Runs 20 minutes before KR analysis job (16:10 KST).
    Ensures cache is hot when analysis job runs.
    """
    KST = pytz.timezone("Asia/Seoul")
    today = datetime.now(KST).date()
    market = "KR"

    from app.infra.db.base import AsyncSessionLocal
    from app.core.container import get_container
    from app.core.config import get_settings

    settings = get_settings()
    container = get_container()

    print(
        f"[CacheWarmup] Starting KR cache warmup "
        f"for {today}"
    )
    warmed = 0
    failed = 0

    async with AsyncSessionLocal() as session:
        market_service = container.market_data_service(
            market, session
        )
        for ticker in settings.kr_tickers:
            try:
                result = await market_service.fetch_and_cache(
                    ticker, market, today
                )
                if result:
                    warmed += 1
                else:
                    failed += 1
            except Exception as e:
                print(
                    f"[CacheWarmup] Failed {ticker}: {e}"
                )
                failed += 1

    print(
        f"[CacheWarmup] KR complete: "
        f"{warmed} warmed, {failed} failed"
    )


async def run_us_cache_warmup() -> None:
    """
    Pre-warm US market data cache at 06:50 KST.
    Runs 20 minutes before US analysis job (07:10 KST).
    Uses previous day's data (US market closed).
    """
    KST = pytz.timezone("Asia/Seoul")
    yesterday = (
        datetime.now(KST) - timedelta(days=1)
    ).date()
    market = "US"

    from app.infra.db.base import AsyncSessionLocal
    from app.core.container import get_container
    from app.core.config import get_settings

    settings = get_settings()
    container = get_container()

    print(
        f"[CacheWarmup] Starting US cache warmup "
        f"for {yesterday}"
    )
    warmed = 0
    failed = 0

    async with AsyncSessionLocal() as session:
        market_service = container.market_data_service(
            market, session
        )
        for ticker in settings.us_tickers:
            try:
                result = await market_service.fetch_and_cache(
                    ticker, market, yesterday
                )
                if result:
                    warmed += 1
                else:
                    failed += 1
            except Exception as e:
                print(
                    f"[CacheWarmup] Failed {ticker}: {e}"
                )
                failed += 1

    print(
        f"[CacheWarmup] US complete: "
        f"{warmed} warmed, {failed} failed"
    )