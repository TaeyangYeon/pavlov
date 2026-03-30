"""
Comprehensive unit tests for cooling-off logic in NotificationService.
All tests should FAIL initially (Red phase) until implementation is complete.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from app.domain.notification.service import NotificationService
from app.domain.notification.interfaces import NotificationPort
from app.infra.db.repositories.notification_repository import NotificationRepository
from app.infra.db.models.notification import Notification, NotificationTypeEnum
from app.core.config import Settings


class TestCoolingOffLogic:
    """Test suite for cooling-off period logic."""

    @pytest.fixture
    def mock_notifier(self):
        """Single mock notifier for cooling-off tests."""
        notifier = Mock(spec=NotificationPort)
        notifier.send = AsyncMock(return_value=True)
        notifier.channel_name = "mock_channel"
        return notifier

    @pytest.fixture
    def mock_repository(self):
        """Mock NotificationRepository."""
        repo = Mock(spec=NotificationRepository)
        repo.get_latest_strategy_alert = AsyncMock()
        return repo

    @pytest.fixture
    def settings_30min_cooling_off(self):
        """Settings with 30-minute cooling-off period."""
        settings = Mock(spec=Settings)
        settings.cooling_off_minutes = 30
        return settings

    @pytest.fixture
    def settings_60min_cooling_off(self):
        """Settings with 60-minute cooling-off period."""
        settings = Mock(spec=Settings)
        settings.cooling_off_minutes = 60
        return settings

    @pytest.fixture
    def notification_service_30min(self, mock_notifier, mock_repository, settings_30min_cooling_off):
        """NotificationService with 30min cooling-off."""
        return NotificationService(
            notifiers=[mock_notifier],
            repository=mock_repository,
            settings=settings_30min_cooling_off,
        )

    @pytest.fixture
    def notification_service_60min(self, mock_notifier, mock_repository, settings_60min_cooling_off):
        """NotificationService with 60min cooling-off."""
        return NotificationService(
            notifiers=[mock_notifier],
            repository=mock_repository,
            settings=settings_60min_cooling_off,
        )

    @pytest.mark.asyncio
    async def test_cooling_off_check_within_period(
        self, notification_service_30min, mock_notifier, mock_repository
    ):
        """Should trigger warning when trade is within cooling-off period."""
        base_time = datetime.now()
        
        # Strategy alert 15 minutes ago (within 30min cooling-off)
        last_alert = Notification(
            id=uuid4(),
            type=NotificationTypeEnum.STRATEGY_CHANGE,
            ticker="AAPL",
            action="buy",
            title="Previous BUY alert",
            body="AI recommended buy",
            created_at=base_time - timedelta(minutes=15),
        )
        mock_repository.get_latest_strategy_alert.return_value = last_alert
        
        # User trades now
        trade_time = base_time
        
        result = await notification_service_30min.check_and_warn_impulse(
            ticker="AAPL",
            trade_time=trade_time,
        )
        
        assert result is True  # Warning triggered
        mock_notifier.send.assert_called_once()
        
        # Verify warning notification content
        warning_notification = mock_notifier.send.call_args[0][0]
        assert warning_notification.type == "impulse_warning"
        assert "AAPL" in warning_notification.title

    @pytest.mark.asyncio
    async def test_cooling_off_check_after_period(
        self, notification_service_30min, mock_notifier, mock_repository
    ):
        """Should NOT trigger warning when trade is after cooling-off period."""
        base_time = datetime.now()
        
        # Strategy alert 45 minutes ago (after 30min cooling-off)
        last_alert = Notification(
            id=uuid4(),
            type=NotificationTypeEnum.STRATEGY_CHANGE,
            ticker="AAPL",
            action="buy",
            title="Previous BUY alert",
            body="AI recommended buy",
            created_at=base_time - timedelta(minutes=45),
        )
        mock_repository.get_latest_strategy_alert.return_value = last_alert
        
        # User trades now (safe to trade)
        trade_time = base_time
        
        result = await notification_service_30min.check_and_warn_impulse(
            ticker="AAPL",
            trade_time=trade_time,
        )
        
        assert result is False  # No warning
        mock_notifier.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_cooling_off_with_no_previous_notification(
        self, notification_service_30min, mock_notifier, mock_repository
    ):
        """Should NOT trigger warning when no previous strategy alert exists."""
        mock_repository.get_latest_strategy_alert.return_value = None
        
        result = await notification_service_30min.check_and_warn_impulse(
            ticker="AAPL",
            trade_time=datetime.now(),
        )
        
        assert result is False
        mock_notifier.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_cooling_off_boundary_exact(
        self, notification_service_30min, mock_notifier, mock_repository
    ):
        """Should NOT trigger at exactly 30 minutes (boundary is safe, use strict <)."""
        base_time = datetime.now()
        
        # Strategy alert exactly 30 minutes ago
        last_alert = Notification(
            id=uuid4(),
            type=NotificationTypeEnum.STRATEGY_CHANGE,
            ticker="AAPL",
            action="buy",
            title="Previous BUY alert",
            body="AI recommended buy",
            created_at=base_time - timedelta(minutes=30),
        )
        mock_repository.get_latest_strategy_alert.return_value = last_alert
        
        trade_time = base_time
        
        result = await notification_service_30min.check_and_warn_impulse(
            ticker="AAPL",
            trade_time=trade_time,
        )
        
        assert result is False  # Boundary is safe
        mock_notifier.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_cooling_off_uses_config_value(
        self, notification_service_60min, mock_notifier, mock_repository
    ):
        """Should use cooling_off_minutes from config correctly."""
        base_time = datetime.now()
        
        # Test case 1: 59 minutes ago with 60min cooling-off → should trigger
        last_alert_59min = Notification(
            id=uuid4(),
            type=NotificationTypeEnum.STRATEGY_CHANGE,
            ticker="AAPL",
            action="buy",
            title="Previous alert",
            body="AI recommendation",
            created_at=base_time - timedelta(minutes=59),
        )
        mock_repository.get_latest_strategy_alert.return_value = last_alert_59min
        
        result = await notification_service_60min.check_and_warn_impulse(
            ticker="AAPL",
            trade_time=base_time,
        )
        
        assert result is True  # Within 60min cooling-off
        mock_notifier.send.assert_called_once()
        
        # Reset mock
        mock_notifier.send.reset_mock()
        
        # Test case 2: 61 minutes ago with 60min cooling-off → should NOT trigger
        last_alert_61min = Notification(
            id=uuid4(),
            type=NotificationTypeEnum.STRATEGY_CHANGE,
            ticker="AAPL",
            action="buy", 
            title="Previous alert",
            body="AI recommendation",
            created_at=base_time - timedelta(minutes=61),
        )
        mock_repository.get_latest_strategy_alert.return_value = last_alert_61min
        
        result = await notification_service_60min.check_and_warn_impulse(
            ticker="AAPL",
            trade_time=base_time,
        )
        
        assert result is False  # After 60min cooling-off
        mock_notifier.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_cooling_off_boundary_conditions(
        self, notification_service_30min, mock_notifier, mock_repository
    ):
        """Test precise boundary conditions for cooling-off logic."""
        base_time = datetime.now()
        
        # Test 29 minutes 59 seconds ago → should trigger
        last_alert_29_59 = Notification(
            id=uuid4(),
            type=NotificationTypeEnum.STRATEGY_CHANGE,
            ticker="AAPL",
            action="buy",
            title="Previous alert",
            body="AI recommendation",
            created_at=base_time - timedelta(minutes=29, seconds=59),
        )
        mock_repository.get_latest_strategy_alert.return_value = last_alert_29_59
        
        result = await notification_service_30min.check_and_warn_impulse(
            ticker="AAPL",
            trade_time=base_time,
        )
        
        assert result is True  # Just under 30min → trigger
        mock_notifier.send.assert_called_once()
        
        # Reset mock
        mock_notifier.send.reset_mock()
        
        # Test 30 minutes 1 second ago → should NOT trigger
        last_alert_30_01 = Notification(
            id=uuid4(),
            type=NotificationTypeEnum.STRATEGY_CHANGE,
            ticker="AAPL",
            action="buy",
            title="Previous alert",
            body="AI recommendation",
            created_at=base_time - timedelta(minutes=30, seconds=1),
        )
        mock_repository.get_latest_strategy_alert.return_value = last_alert_30_01
        
        result = await notification_service_30min.check_and_warn_impulse(
            ticker="AAPL",
            trade_time=base_time,
        )
        
        assert result is False  # Just over 30min → safe
        mock_notifier.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_cooling_off_different_tickers_isolated(
        self, notification_service_30min, mock_notifier, mock_repository
    ):
        """Should check cooling-off period per ticker independently."""
        base_time = datetime.now()
        
        # Previous alert for AAPL 10 minutes ago
        last_alert_aapl = Notification(
            id=uuid4(),
            type=NotificationTypeEnum.STRATEGY_CHANGE,
            ticker="AAPL",
            action="buy",
            title="AAPL alert",
            body="AI recommendation",
            created_at=base_time - timedelta(minutes=10),
        )
        
        # Mock repository to return AAPL alert when asked for AAPL
        def mock_get_latest(ticker):
            if ticker == "AAPL":
                return last_alert_aapl
            return None  # No alert for other tickers
        
        mock_repository.get_latest_strategy_alert.side_effect = mock_get_latest
        
        # Check cooling-off for AAPL → should trigger
        result_aapl = await notification_service_30min.check_and_warn_impulse(
            ticker="AAPL",
            trade_time=base_time,
        )
        
        assert result_aapl is True
        
        # Check cooling-off for MSFT → should NOT trigger (no previous alert)
        result_msft = await notification_service_30min.check_and_warn_impulse(
            ticker="MSFT", 
            trade_time=base_time,
        )
        
        assert result_msft is False