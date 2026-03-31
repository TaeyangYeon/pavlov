"""
Behavior analytics API endpoints for emotional suppression system.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.config import get_settings
from app.domain.behavior.analyzer import BehaviorAnalyzer
from app.domain.behavior.cooling_off import CoolingOffGate
from app.domain.behavior.schemas import BehaviorReportResponse
from app.infra.db.repositories.decision_log_repository import DecisionLogRepository
from app.infra.db.repositories.notification_repository import NotificationRepository

# Stub user ID for demonstration - in real app would come from auth
STUB_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

router = APIRouter(prefix="/behavior", tags=["behavior"])


@router.get(
    "/report",
    response_model=BehaviorReportResponse
)
async def get_behavior_report(
    days: int = Query(default=30, le=365),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Generate behavioral analysis report for current user.
    Includes AI alignment rate, impulse patterns,
    overtrading detection.
    """
    decision_repo = DecisionLogRepository(session)
    analyzer = BehaviorAnalyzer()

    rows = await decision_repo.get_by_user(STUB_USER_ID, days=days)
    decisions = [
        {
            "ticker": r.ticker,
            "action": str(
                r.action.value
                if hasattr(r.action, 'value')
                else r.action
            ),
            "price": float(r.price),
            "quantity": float(r.quantity),
            "ai_suggested": r.ai_suggested,
            "notes": r.notes or "",
            "created_at": r.created_at,
        }
        for r in rows
    ]

    report = analyzer.analyze(
        user_id=str(STUB_USER_ID),
        decisions=decisions,
        analysis_period_days=days,
    )

    # Build alignment label and color
    rate = report.ai_alignment_rate
    if rate >= 0.9:
        label = "AI 추천을 잘 따르고 있습니다"
        color = "green"
    elif rate >= 0.7:
        label = "가끔 AI와 다른 판단을 하고 있습니다"
        color = "yellow"
    elif rate >= 0.5:
        label = "AI 추천을 절반 정도만 따르고 있습니다"
        color = "orange"
    else:
        label = "AI 추천과 자주 반대로 행동하고 있습니다"
        color = "red"

    return BehaviorReportResponse(
        total_trades=report.total_trades,
        ai_alignment_rate=report.ai_alignment_rate,
        ai_alignment_pct=f"{rate * 100:.1f}%",
        alignment_label=label,
        alignment_color=color,
        impulse_trade_count=report.impulse_trade_count,
        contradiction_count=report.contradiction_count,
        overtrading_tickers=report.overtrading_tickers,
        avg_holding_days=report.avg_holding_days,
        most_traded_ticker=report.most_traded_ticker,
        cooling_off_warnings_received=(
            report.cooling_off_warnings_received
        ),
        patterns=[
            {
                "type": p.pattern_type,
                "ticker": p.ticker,
                "description": p.description,
                "detected_at": p.detected_at.isoformat(),
            }
            for p in report.patterns
        ],
        analysis_period_days=report.analysis_period_days,
        generated_at=report.generated_at.isoformat(),
    )


@router.get("/cooling-off/{ticker}")
async def check_cooling_off(
    ticker: str,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Check cooling-off status for a ticker.
    Called by frontend before showing trade form.
    """
    notification_repo = NotificationRepository(session)
    cooling_gate = CoolingOffGate()
    settings = get_settings()

    last_alert = await notification_repo.get_latest_strategy_alert(ticker)

    result = cooling_gate.check(
        ticker=ticker,
        trade_time=datetime.now(),
        last_alert_time=(
            last_alert.created_at.replace(tzinfo=None)
            if last_alert else None
        ),
        last_ai_recommendation=(
            last_alert.action if last_alert else None
        ),
        cooling_off_minutes=settings.cooling_off_minutes,
    )

    return {
        "ticker": ticker,
        "is_within_cooling_off": (
            result.is_within_cooling_off
        ),
        "minutes_elapsed": result.minutes_elapsed,
        "minutes_remaining": result.minutes_remaining,
        "cooling_off_minutes": result.cooling_off_minutes,
        "last_ai_recommendation": (
            result.last_ai_recommendation
        ),
    }