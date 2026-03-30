"""
Unit tests for InAppNotifier following TDD approach.
All tests should FAIL initially (Red phase) until implementation is complete.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from app.domain.notification.schemas import NotificationCreate
from app.infra.notification.in_app_notifier import InAppNotifier
from app.infra.db.repositories.notification_repository import NotificationRepository
from app.infra.db.models.notification import Notification, NotificationTypeEnum


class TestInAppNotifier:
    """Test suite for InAppNotifier."""

    @pytest.fixture
    def mock_repository(self):
        """Mock NotificationRepository."""
        repo = Mock(spec=NotificationRepository)
        repo.save = AsyncMock()
        return repo

    @pytest.fixture
    def in_app_notifier(self, mock_repository):
        """InAppNotifier instance for testing."""
        return InAppNotifier(repository=mock_repository)

    @pytest.fixture
    def sample_notification_create(self):
        """Sample NotificationCreate for testing."""
        return NotificationCreate(
            type="strategy_change",
            title="🟢 AAPL — BUY",
            body="시장: US | 신뢰도: 85% | 근거: Strong technical breakout",
            ticker="AAPL",
            action="buy",
            user_id=uuid4(),
        )

    @pytest.mark.asyncio
    async def test_in_app_notifier_saves_to_db(
        self, in_app_notifier, mock_repository, sample_notification_create
    ):
        """Should call repository.save() with correct notification data."""
        # Mock successful save
        mock_repository.save.return_value = Notification(
            id=uuid4(),
            type=NotificationTypeEnum.STRATEGY_CHANGE,
            title=sample_notification_create.title,
            body=sample_notification_create.body,
            ticker=sample_notification_create.ticker,
            action=sample_notification_create.action,
            user_id=sample_notification_create.user_id,
            is_read=False,
        )
        
        result = await in_app_notifier.send(sample_notification_create)
        
        # Should call save with the notification
        mock_repository.save.assert_called_once_with(sample_notification_create)
        assert result is True

    @pytest.mark.asyncio
    async def test_in_app_notifier_returns_true_on_success(
        self, in_app_notifier, mock_repository, sample_notification_create
    ):
        """Should return True when save is successful."""
        mock_repository.save.return_value = Mock()
        
        result = await in_app_notifier.send(sample_notification_create)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_in_app_notifier_returns_false_on_db_error(
        self, in_app_notifier, mock_repository, sample_notification_create
    ):
        """Should return False when repository raises exception (not raise)."""
        # Mock repository to raise exception
        mock_repository.save.side_effect = Exception("Database connection failed")
        
        result = await in_app_notifier.send(sample_notification_create)
        
        # Should return False, not raise exception
        assert result is False

    def test_in_app_channel_name(self, in_app_notifier):
        """Should return correct channel name."""
        assert in_app_notifier.channel_name == "in_app"