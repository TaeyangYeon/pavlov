import pytest


@pytest.mark.integration
async def test_kr_strategy_notification_has_kr_ticker(db_session):
    """
    Notification from KR strategy must contain KR ticker.
    Must not contain US ticker format.
    """
    from app.infra.db.repositories.notification_repository import NotificationRepository
    from app.infra.notification.in_app_notifier import InAppNotifier
    from app.domain.notification.schemas import NotificationCreate

    repo = NotificationRepository(db_session)
    notifier = InAppNotifier(repo)

    kr_notification = NotificationCreate(
        type="strategy_change",
        title="⏸️ 005930 — HOLD",
        body="시장: KR | 신뢰도: 80%",
        ticker="005930",
        action="hold",
    )

    await notifier.send(kr_notification)

    # Verify saved correctly
    notifications = await repo.get_unread(limit=5)
    kr_notifs = [n for n in notifications if n.ticker == "005930"]
    assert len(kr_notifs) == 1
    assert kr_notifs[0].ticker == "005930"
    assert kr_notifs[0].ticker.isdigit()  # KR format


@pytest.mark.integration
async def test_us_strategy_notification_has_us_ticker(db_session):
    """US strategy notification must have US ticker."""
    from app.infra.db.repositories.notification_repository import NotificationRepository
    from app.infra.notification.in_app_notifier import InAppNotifier
    from app.domain.notification.schemas import NotificationCreate

    repo = NotificationRepository(db_session)
    notifier = InAppNotifier(repo)

    us_notification = NotificationCreate(
        type="strategy_change",
        title="🟢 AAPL — BUY",
        body="Market: US | Confidence: 75%",
        ticker="AAPL",
        action="buy",
    )

    await notifier.send(us_notification)

    notifications = await repo.get_unread(limit=5)
    us_notifs = [n for n in notifications if n.ticker == "AAPL"]
    assert len(us_notifs) == 1
    assert us_notifs[0].ticker == "AAPL"
    assert not us_notifs[0].ticker.isdigit()  # US format


@pytest.mark.integration
async def test_kr_and_us_notifications_retrievable_together(db_session):
    """
    Both KR and US notifications coexist in DB.
    get_unread must return both without market filtering.
    """
    from app.infra.db.repositories.notification_repository import NotificationRepository
    from app.domain.notification.schemas import NotificationCreate

    repo = NotificationRepository(db_session)

    await repo.save(NotificationCreate(
        type="strategy_change",
        title="KR Alert", body="KR body",
        ticker="005930", action="hold",
    ))
    await repo.save(NotificationCreate(
        type="tp_sl_alert",
        title="US Alert", body="US body",
        ticker="AAPL", action="partial_sell",
    ))

    all_notifs = await repo.get_unread(limit=10)
    tickers = {n.ticker for n in all_notifs}

    assert "005930" in tickers
    assert "AAPL" in tickers