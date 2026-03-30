"""
Unit tests for NotificationService following TDD approach.
All tests should FAIL initially (Red phase) until implementation is complete.
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from app.domain.notification.interfaces import NotificationPort
from app.domain.notification.schemas import NotificationCreate
from app.domain.notification.service import NotificationService
from app.domain.strategy.schemas import UnifiedStrategy, StrategyRunResult
from app.domain.position.schemas import TpSlEvaluationResponse
from app.infra.db.repositories.notification_repository import NotificationRepository
from app.infra.db.models.notification import Notification, NotificationTypeEnum
from app.core.config import Settings


class TestNotificationService:
    """Test suite for NotificationService."""

    @pytest.fixture
    def mock_notifiers(self):
        """Mock notifiers for testing."""
        notifier1 = Mock(spec=NotificationPort)
        notifier1.send = AsyncMock(return_value=True)
        notifier1.channel_name = "mock_channel_1"
        
        notifier2 = Mock(spec=NotificationPort)
        notifier2.send = AsyncMock(return_value=True)
        notifier2.channel_name = "mock_channel_2"
        
        return [notifier1, notifier2]

    @pytest.fixture
    def mock_repository(self):
        """Mock NotificationRepository."""
        repo = Mock(spec=NotificationRepository)
        repo.save = AsyncMock()
        repo.get_latest_strategy_alert = AsyncMock(return_value=None)
        return repo

    @pytest.fixture
    def mock_settings(self):
        """Mock settings with cooling off configuration."""
        settings = Mock(spec=Settings)
        settings.cooling_off_minutes = 30
        return settings

    @pytest.fixture
    def notification_service(self, mock_notifiers, mock_repository, mock_settings):
        """NotificationService instance for testing."""
        return NotificationService(
            notifiers=mock_notifiers,
            repository=mock_repository,
            settings=mock_settings,
        )

    @pytest.fixture
    def sample_strategy_run_result(self):
        """Sample StrategyRunResult with mixed changed_from_last values."""
        strategies = [
            UnifiedStrategy(
                ticker="AAPL",
                market="US",
                final_action="buy",
                action_source="ai",
                confidence=Decimal("0.85"),
                rationale="Strong technical breakout",
                changed_from_last=True,  # Should trigger notification
            ),
            UnifiedStrategy(
                ticker="MSFT",
                market="US", 
                final_action="hold",
                action_source="ai",
                confidence=Decimal("0.60"),
                rationale="Sideways consolidation",
                changed_from_last=False,  # Should NOT trigger notification
            ),
            UnifiedStrategy(
                ticker="GOOGL",
                market="US",
                final_action="partial_sell",
                action_source="position_engine",
                confidence=Decimal("0.75"),
                rationale="Take profit target reached",
                changed_from_last=True,  # Should trigger notification
            ),
        ]
        
        return StrategyRunResult(
            market="US",
            run_date=date.today(),
            strategies=strategies,
            total_tickers_analyzed=3,
            changed_count=2,
            analysis_log_id=uuid4(),
        )

    @pytest.fixture
    def sample_tp_sl_response(self):
        """Sample TpSlEvaluationResponse for testing."""
        return TpSlEvaluationResponse(
            position_id=uuid4(),
            ticker="AAPL",
            action="partial_sell",
            triggered_by="take_profit",
            triggered_level_pct=Decimal("15.0"),
            sell_quantity=Decimal("50.0"),
            sell_ratio=Decimal("0.5"),
            current_pnl_pct=Decimal("15.2"),
            realized_pnl_estimate=Decimal("750.00"),
            avg_price=Decimal("150.00"),
            current_price=Decimal("172.80"),
            total_quantity=Decimal("100.0"),
        )

    # ─── STRATEGY CHANGE NOTIFICATIONS ───

    @pytest.mark.asyncio
    async def test_notify_strategy_run_sends_for_changed_only(
        self, notification_service, mock_notifiers, sample_strategy_run_result
    ):
        """Should send notifications only for strategies with changed_from_last=True."""
        await notification_service.notify_strategy_run(sample_strategy_run_result)
        
        # Should call send() exactly 2 times (for AAPL and GOOGL only)
        assert mock_notifiers[0].send.call_count == 2
        assert mock_notifiers[1].send.call_count == 2
        
        # Verify notification content for first changed strategy (AAPL)
        call_args_list = mock_notifiers[0].send.call_args_list
        first_call_notification = call_args_list[0][0][0]  # First arg of first call
        assert first_call_notification.type == "strategy_change"
        assert "AAPL" in first_call_notification.title
        assert first_call_notification.ticker == "AAPL"
        assert first_call_notification.action == "buy"

    @pytest.mark.asyncio
    async def test_notify_strategy_run_sends_nothing_if_no_changes(
        self, notification_service, mock_notifiers
    ):
        """Should not send notifications when all changed_from_last=False."""
        strategies = [
            UnifiedStrategy(
                ticker="AAPL",
                market="US",
                final_action="hold", 
                action_source="ai",
                confidence=Decimal("0.60"),
                rationale="No change",
                changed_from_last=False,
            ),
        ]
        
        result = StrategyRunResult(
            market="US",
            run_date=date.today(),
            strategies=strategies,
            total_tickers_analyzed=1,
            changed_count=0,
        )
        
        await notification_service.notify_strategy_run(result)
        
        # Should NOT call send() at all
        mock_notifiers[0].send.assert_not_called()
        mock_notifiers[1].send.assert_not_called()

    @pytest.mark.asyncio
    async def test_notify_strategy_change_content(
        self, notification_service, mock_notifiers
    ):
        """Should create properly formatted notification content."""
        strategy = UnifiedStrategy(
            ticker="TSLA",
            market="US",
            final_action="full_exit",
            action_source="ai",
            confidence=Decimal("0.92"),
            rationale="Risk management exit signal",
            changed_from_last=True,
        )
        
        result = StrategyRunResult(
            market="US",
            run_date=date.today(),
            strategies=[strategy],
            total_tickers_analyzed=1,
            changed_count=1,
        )
        
        await notification_service.notify_strategy_run(result)
        
        notification = mock_notifiers[0].send.call_args[0][0]
        
        assert notification.type == "strategy_change"
        assert "TSLA" in notification.title
        assert "FULL_EXIT" in notification.title
        assert "US" in notification.body
        assert "92%" in notification.body
        assert "Risk management exit signal" in notification.body
        assert notification.ticker == "TSLA"
        assert notification.action == "full_exit"

    @pytest.mark.asyncio
    async def test_notify_strategy_includes_confidence(
        self, notification_service, mock_notifiers
    ):
        """Should include confidence percentage in notification body."""
        strategy = UnifiedStrategy(
            ticker="NVDA",
            market="US", 
            final_action="buy",
            action_source="ai",
            confidence=Decimal("0.73"),
            rationale="AI breakout pattern",
            changed_from_last=True,
        )
        
        result = StrategyRunResult(
            market="US",
            run_date=date.today(),
            strategies=[strategy],
            total_tickers_analyzed=1,
            changed_count=1,
        )
        
        await notification_service.notify_strategy_run(result)
        
        notification = mock_notifiers[0].send.call_args[0][0]
        assert "73%" in notification.body

    # ─── TP/SL ALERT NOTIFICATIONS ───

    @pytest.mark.asyncio
    async def test_notify_tp_sl_sends_on_triggered(
        self, notification_service, mock_notifiers, sample_tp_sl_response
    ):
        """Should send notification when TP/SL action != 'hold'."""
        await notification_service.notify_tp_sl_alert(sample_tp_sl_response)
        
        # Should call send() once for each notifier
        assert mock_notifiers[0].send.call_count == 1
        assert mock_notifiers[1].send.call_count == 1
        
        notification = mock_notifiers[0].send.call_args[0][0]
        assert notification.type == "tp_sl_alert"

    @pytest.mark.asyncio
    async def test_notify_tp_sl_skips_on_hold(
        self, notification_service, mock_notifiers
    ):
        """Should NOT send notification when action = 'hold'."""
        tp_sl_response = TpSlEvaluationResponse(
            position_id=uuid4(),
            ticker="AAPL",
            action="hold",
            triggered_by="none",
            triggered_level_pct=None,
            sell_quantity=Decimal("0.0"),
            sell_ratio=Decimal("0.0"),
            current_pnl_pct=Decimal("5.0"),
            realized_pnl_estimate=Decimal("0.0"),
            avg_price=Decimal("150.00"),
            current_price=Decimal("157.50"),
            total_quantity=Decimal("100.0"),
        )
        
        await notification_service.notify_tp_sl_alert(tp_sl_response)
        
        # Should NOT call send() at all
        mock_notifiers[0].send.assert_not_called()
        mock_notifiers[1].send.assert_not_called()

    @pytest.mark.asyncio
    async def test_notify_tp_sl_content(
        self, notification_service, mock_notifiers, sample_tp_sl_response
    ):
        """Should include all required TP/SL details in notification."""
        await notification_service.notify_tp_sl_alert(sample_tp_sl_response)
        
        notification = mock_notifiers[0].send.call_args[0][0]
        
        assert notification.type == "tp_sl_alert"
        assert "AAPL" in notification.title
        assert "TAKE_PROFIT" in notification.title.upper()
        assert "PARTIAL_SELL" in notification.title.upper()
        
        assert "15.0%" in notification.body  # triggered_level_pct
        assert "50.0" in notification.body    # sell_quantity
        assert "750.00" in notification.body  # realized_pnl_estimate
        
        assert notification.ticker == "AAPL"
        assert notification.action == "partial_sell"

    # ─── IMPULSE WARNING ───

    @pytest.mark.asyncio
    async def test_impulse_warning_triggered_within_cooling_off(
        self, notification_service, mock_notifiers, mock_repository
    ):
        """Should send impulse warning when trade is within cooling-off period."""
        # Mock previous strategy alert 10 minutes ago
        last_alert = Notification(
            id=uuid4(),
            type=NotificationTypeEnum.STRATEGY_CHANGE,
            ticker="AAPL",
            action="buy",
            title="Previous alert",
            body="Previous alert body",
            created_at=datetime.now().replace(minute=datetime.now().minute - 10),
        )
        mock_repository.get_latest_strategy_alert.return_value = last_alert
        
        # User makes trade now (within 30min cooling-off)
        trade_time = datetime.now()
        
        result = await notification_service.check_and_warn_impulse(
            ticker="AAPL",
            trade_time=trade_time,
        )
        
        assert result is True  # Warning was sent
        assert mock_notifiers[0].send.call_count == 1
        
        notification = mock_notifiers[0].send.call_args[0][0]
        assert notification.type == "impulse_warning"
        assert "주의" in notification.title or "Warning" in notification.title
        assert "AAPL" in notification.title

    @pytest.mark.asyncio
    async def test_impulse_warning_not_triggered_after_cooling_off(
        self, notification_service, mock_notifiers, mock_repository
    ):
        """Should NOT send warning when trade is after cooling-off period."""
        # Mock previous strategy alert 45 minutes ago (> 30min cooling-off)
        last_alert = Notification(
            id=uuid4(),
            type=NotificationTypeEnum.STRATEGY_CHANGE,
            ticker="AAPL",
            action="buy",
            title="Previous alert",
            body="Previous alert body",
            created_at=datetime.now().replace(minute=datetime.now().minute - 45),
        )
        mock_repository.get_latest_strategy_alert.return_value = last_alert
        
        trade_time = datetime.now()
        
        result = await notification_service.check_and_warn_impulse(
            ticker="AAPL",
            trade_time=trade_time,
        )
        
        assert result is False  # No warning sent
        mock_notifiers[0].send.assert_not_called()

    @pytest.mark.asyncio
    async def test_impulse_warning_at_exact_boundary(
        self, notification_service, mock_notifiers, mock_repository
    ):
        """Should NOT trigger warning at exactly 30 minutes (boundary = safe)."""
        # Mock previous strategy alert exactly 30 minutes ago
        last_alert = Notification(
            id=uuid4(),
            type=NotificationTypeEnum.STRATEGY_CHANGE,
            ticker="AAPL",
            action="buy",
            title="Previous alert",
            body="Previous alert body",
            created_at=datetime.now().replace(minute=datetime.now().minute - 30),
        )
        mock_repository.get_latest_strategy_alert.return_value = last_alert
        
        trade_time = datetime.now()
        
        result = await notification_service.check_and_warn_impulse(
            ticker="AAPL",
            trade_time=trade_time,
        )
        
        assert result is False  # No warning (boundary is safe)
        mock_notifiers[0].send.assert_not_called()

    @pytest.mark.asyncio
    async def test_impulse_warning_no_previous_alert(
        self, notification_service, mock_notifiers, mock_repository
    ):
        """Should NOT trigger warning when no previous strategy alert exists."""
        mock_repository.get_latest_strategy_alert.return_value = None
        
        result = await notification_service.check_and_warn_impulse(
            ticker="AAPL",
            trade_time=datetime.now(),
        )
        
        assert result is False
        mock_notifiers[0].send.assert_not_called()

    @pytest.mark.asyncio
    async def test_impulse_warning_content(
        self, notification_service, mock_notifiers, mock_repository
    ):
        """Should include original AI recommendation in impulse warning."""
        last_alert = Notification(
            id=uuid4(),
            type=NotificationTypeEnum.STRATEGY_CHANGE,
            ticker="AAPL",
            action="buy",
            title="Previous alert",
            body="Previous alert body",
            created_at=datetime.now().replace(minute=datetime.now().minute - 10),
        )
        mock_repository.get_latest_strategy_alert.return_value = last_alert
        
        await notification_service.check_and_warn_impulse(
            ticker="AAPL",
            trade_time=datetime.now(),
        )
        
        notification = mock_notifiers[0].send.call_args[0][0]
        
        assert notification.type == "impulse_warning"
        assert "주의" in notification.title or "Warning" in notification.title
        assert "buy" in notification.body  # Original AI recommendation
        assert "30분" in notification.body  # Cooling-off period

    # ─── MULTI-CHANNEL ───

    @pytest.mark.asyncio
    async def test_service_sends_to_all_notifiers(
        self, notification_service, mock_notifiers
    ):
        """Should send notification to ALL configured notifiers."""
        strategy = UnifiedStrategy(
            ticker="AAPL",
            market="US",
            final_action="buy",
            action_source="ai",
            confidence=Decimal("0.80"),
            rationale="Test",
            changed_from_last=True,
        )
        
        result = StrategyRunResult(
            market="US",
            run_date=date.today(),
            strategies=[strategy],
            total_tickers_analyzed=1,
            changed_count=1,
        )
        
        await notification_service.notify_strategy_run(result)
        
        # BOTH notifiers should be called
        assert mock_notifiers[0].send.call_count == 1
        assert mock_notifiers[1].send.call_count == 1

    @pytest.mark.asyncio
    async def test_service_continues_if_one_notifier_fails(
        self, notification_service, mock_notifiers
    ):
        """Should continue sending to other notifiers if one fails."""
        # Make first notifier raise exception
        mock_notifiers[0].send.side_effect = Exception("Notifier 1 failed")
        
        strategy = UnifiedStrategy(
            ticker="AAPL",
            market="US",
            final_action="buy",
            action_source="ai",
            confidence=Decimal("0.80"),
            rationale="Test",
            changed_from_last=True,
        )
        
        result = StrategyRunResult(
            market="US",
            run_date=date.today(),
            strategies=[strategy],
            total_tickers_analyzed=1,
            changed_count=1,
        )
        
        # Should not raise exception
        await notification_service.notify_strategy_run(result)
        
        # First notifier should have been called (and failed)
        assert mock_notifiers[0].send.call_count == 1
        
        # Second notifier should still be called successfully
        assert mock_notifiers[1].send.call_count == 1