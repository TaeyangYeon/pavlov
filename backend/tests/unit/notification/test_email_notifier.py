"""
Unit tests for EmailNotifier following TDD approach.
All tests should FAIL initially (Red phase) until implementation is complete.
"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from app.domain.notification.schemas import NotificationCreate
from app.infra.notification.email_notifier import EmailNotifier
from app.core.config import Settings


class TestEmailNotifier:
    """Test suite for EmailNotifier."""

    @pytest.fixture
    def settings_email_enabled(self):
        """Settings with email enabled."""
        settings = Mock(spec=Settings)
        settings.email_enabled = True
        settings.email_host = "smtp.gmail.com"
        settings.email_port = 587
        settings.email_user = "test@gmail.com"
        settings.email_password = "test_password"
        settings.email_to = "recipient@gmail.com"
        return settings

    @pytest.fixture
    def settings_email_disabled(self):
        """Settings with email disabled."""
        settings = Mock(spec=Settings)
        settings.email_enabled = False
        return settings

    @pytest.fixture
    def email_notifier_enabled(self, settings_email_enabled):
        """EmailNotifier with email enabled."""
        return EmailNotifier(settings=settings_email_enabled)

    @pytest.fixture
    def email_notifier_disabled(self, settings_email_disabled):
        """EmailNotifier with email disabled."""
        return EmailNotifier(settings=settings_email_disabled)

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
    async def test_email_notifier_returns_false_when_disabled(
        self, email_notifier_disabled, sample_notification_create
    ):
        """Should return False immediately when EMAIL_ENABLED=false."""
        result = await email_notifier_disabled.send(sample_notification_create)
        
        assert result is False

    @pytest.mark.asyncio
    @patch('smtplib.SMTP')
    async def test_email_notifier_sends_when_enabled(
        self, mock_smtp, email_notifier_enabled, sample_notification_create
    ):
        """Should attempt to send email when EMAIL_ENABLED=true."""
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = await email_notifier_enabled.send(sample_notification_create)
        
        assert result is True
        
        # Verify SMTP connection was made
        mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@gmail.com", "test_password")
        mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    @patch('smtplib.SMTP')
    async def test_email_notifier_returns_false_on_smtp_error(
        self, mock_smtp, email_notifier_enabled, sample_notification_create
    ):
        """Should return False (not raise) when SMTP fails."""
        # Mock SMTP to raise exception
        mock_smtp.side_effect = Exception("SMTP connection failed")
        
        result = await email_notifier_enabled.send(sample_notification_create)
        
        # Should return False, not raise
        assert result is False

    @pytest.mark.asyncio
    async def test_email_notifier_formats_subject_correctly(
        self, email_notifier_enabled, sample_notification_create
    ):
        """Should format email subject with [pavlov] prefix."""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            await email_notifier_enabled.send(sample_notification_create)
            
            # Check that send_message was called
            mock_server.send_message.assert_called_once()
            
            # Get the email message that was sent
            email_msg = mock_server.send_message.call_args[0][0]
            
            assert email_msg["Subject"] == "[pavlov] 🟢 AAPL — BUY"
            assert email_msg["From"] == "test@gmail.com"
            assert email_msg["To"] == "recipient@gmail.com"

    def test_email_channel_name(self, email_notifier_enabled):
        """Should return correct channel name."""
        assert email_notifier_enabled.channel_name == "email"