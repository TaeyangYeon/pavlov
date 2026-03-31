"""
Decision recording API endpoints for behavioral analysis system.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.container import get_container
from app.core.config import get_settings
from app.domain.behavior.cooling_off import CoolingOffGate
from app.domain.behavior.schemas import DecisionCreate, DecisionResponse
from app.infra.db.repositories.decision_log_repository import DecisionLogRepository
from app.infra.db.repositories.notification_repository import NotificationRepository

# Stub user ID for demonstration - in real app would come from auth
STUB_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.post(
    "/",
    response_model=DecisionResponse,
    status_code=201
)
async def record_decision(
    data: DecisionCreate,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Record a user trading decision.
    Checks cooling-off period and AI alignment.
    """
    container = get_container()
    decision_repo = DecisionLogRepository(session)
    notification_repo = NotificationRepository(session)
    cooling_gate = CoolingOffGate()
    settings = get_settings()

    # Step 1: Check cooling-off period
    last_alert = await notification_repo.get_latest_strategy_alert(data.ticker)
    cooling_result = cooling_gate.check(
        ticker=data.ticker,
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

    cooling_warning = cooling_result.is_within_cooling_off
    notes = data.notes or ""

    # Step 2: Handle cooling-off override
    if cooling_warning and data.override_cooling_off:
        notes = (
            f"[Cooling-off override: "
            f"{cooling_result.minutes_elapsed:.0f}min after alert] "
            + notes
        )[:500]
    elif cooling_warning and not data.override_cooling_off:
        # Frontend should have shown warning — still allow
        # but note it wasn't explicitly overridden
        notes = (
            f"[Cooling-off: "
            f"{cooling_result.minutes_remaining:.0f}min remaining] "
            + notes
        )[:500]

    # Step 3: Determine AI alignment
    ai_suggested = False
    if last_alert and last_alert.action:
        # Map notification action to decision alignment
        if last_alert.action == data.action:
            ai_suggested = True
        elif (
            last_alert.action in ("hold", "full_exit")
            and data.action == "buy"
        ):
            ai_suggested = False
        elif (
            last_alert.action == "buy"
            and data.action == "sell"
        ):
            ai_suggested = False

    # Step 4: Send impulse warning if cooling-off
    if cooling_warning:
        notification_service = container.notification_service(session)
        await notification_service.check_and_warn_impulse(
            ticker=data.ticker,
            trade_time=datetime.now(),
        )

    # Step 5: Record decision
    row = await decision_repo.record(
        user_id=STUB_USER_ID,
        ticker=data.ticker,
        action=data.action,
        price=data.price,
        quantity=data.quantity,
        ai_suggested=ai_suggested,
        notes=notes or None,
    )

    return DecisionResponse(
        id=row.id,
        ticker=row.ticker,
        action=str(row.action.value if hasattr(row.action, 'value') else row.action),
        price=row.price,
        quantity=row.quantity,
        ai_suggested=row.ai_suggested,
        cooling_off_warning=cooling_warning,
        notes=row.notes,
        created_at=row.created_at,
    )


@router.get(
    "/",
    response_model=list[DecisionResponse]
)
async def list_decisions(
    ticker: str | None = Query(default=None),
    days: int = Query(default=30, le=365),
    session: AsyncSession = Depends(get_db_session),
):
    """List user trading decisions."""
    decision_repo = DecisionLogRepository(session)
    if ticker:
        rows = await decision_repo.get_by_ticker(STUB_USER_ID, ticker)
    else:
        rows = await decision_repo.get_by_user(STUB_USER_ID, days=days)
    
    return [
        DecisionResponse(
            id=r.id, 
            ticker=r.ticker, 
            action=str(r.action.value if hasattr(r.action, 'value') else r.action),
            price=r.price, 
            quantity=r.quantity,
            ai_suggested=r.ai_suggested,
            cooling_off_warning=False,
            notes=r.notes, 
            created_at=r.created_at,
        )
        for r in rows
    ]