"""
NotificationService implementation.
Core business logic for notification orchestration.
"""

from datetime import datetime

from app.core.config import Settings
from app.domain.position.schemas import TpSlEvaluationResponse
from app.domain.strategy.schemas import StrategyRunResult
from app.infra.db.repositories.notification_repository import NotificationRepository

from .interfaces import NotificationPort
from .schemas import NotificationCreate


class NotificationService:
    """
    Orchestrates notification delivery across all channels.
    
    Single responsibility: routing + cooling-off logic.
    Depends on abstractions (NotificationPort list) for extensibility.
    """
    
    def __init__(
        self,
        notifiers: list[NotificationPort],
        repository: NotificationRepository,
        settings: Settings,
    ):
        """
        Initialize the notification service.
        
        Args:
            notifiers: List of notification channels to send through
            repository: Repository for database operations
            settings: Application settings with cooling-off configuration
        """
        self._notifiers = notifiers
        self._repository = repository
        self._settings = settings

    async def notify_strategy_run(self, result: StrategyRunResult) -> None:
        """
        Send notifications for changed strategies only.
        One notification per changed ticker.
        
        Args:
            result: Strategy run result with all ticker strategies
        """
        for strategy in result.strategies:
            if not strategy.changed_from_last:
                continue  # Skip unchanged strategies

            # Map action to emoji for better UX
            action_emoji = {
                "hold": "⏸️",
                "buy": "🟢", 
                "partial_sell": "🟡",
                "full_exit": "🔴",
            }.get(strategy.final_action, "")

            # Create notification title (max 100 chars)
            title = (
                f"{action_emoji} {strategy.ticker} — "
                f"{strategy.final_action.upper()}"
            )[:100]

            # Create notification body with key details (max 500 chars)
            body = (
                f"시장: {strategy.market} | "
                f"신뢰도: {strategy.confidence:.0%} | "
                f"근거: {strategy.rationale}"
            )[:500]

            notification = NotificationCreate(
                type="strategy_change",
                title=title,
                body=body,
                ticker=strategy.ticker,
                action=strategy.final_action,
            )
            
            await self._send_to_all(notification)

    async def notify_tp_sl_alert(self, result: TpSlEvaluationResponse) -> None:
        """
        Send notification when TP/SL is triggered.
        Skipped if action = "hold".
        
        Args:
            result: TP/SL evaluation result
        """
        if result.action == "hold":
            return  # No notification needed

        # Create alert title with trigger type
        trigger_type = result.triggered_by.upper()
        title = (
            f"🚨 {result.ticker} — "
            f"{trigger_type} Triggered: "
            f"{result.action.upper()}"
        )[:100]

        # Create detailed body with execution info
        body = (
            f"트리거 레벨: {result.triggered_level_pct}% | "
            f"매도 수량: {result.sell_quantity} | "
            f"예상 실현 손익: {result.realized_pnl_estimate}"
        )[:500]

        notification = NotificationCreate(
            type="tp_sl_alert",
            title=title,
            body=body,
            ticker=result.ticker,
            action=result.action,
        )
        
        await self._send_to_all(notification)

    async def check_and_warn_impulse(
        self,
        ticker: str,
        trade_time: datetime,
    ) -> bool:
        """
        Check if trade is within cooling-off period and send warning.
        
        This is the "emotional restraint device" (감정 억제 장치) that warns
        users when they attempt to trade contrary to recent AI recommendations.
        
        Args:
            ticker: Stock ticker being traded
            trade_time: When the trade attempt was made
            
        Returns:
            bool: True if warning was sent, False otherwise
        """
        # Find the most recent strategy alert for this ticker
        last_alert = await self._repository.get_latest_strategy_alert(ticker)
        
        if last_alert is None:
            return False  # No previous alert, no warning needed
        
        # Calculate time elapsed since last alert
        # Remove timezone info for comparison (both should be naive datetimes)
        alert_time = last_alert.created_at.replace(tzinfo=None)
        elapsed = trade_time - alert_time
        elapsed_minutes = elapsed.total_seconds() / 60
        
        # Check if within cooling-off period (strict <, boundary is safe)
        if elapsed_minutes >= self._settings.cooling_off_minutes:
            return False  # Outside cooling-off period, trade is allowed
        
        # Within cooling-off period → send impulse warning
        title = f"⚠️ {ticker} — 충동 거래 주의"[:100]
        
        body = (
            f"최근 전략 알림({int(elapsed_minutes)}분 전)과 "
            f"다른 행동을 하려 합니다. "
            f"AI 추천: {last_alert.action or 'N/A'} | "
            f"냉각 기간: {self._settings.cooling_off_minutes}분"
        )[:500]

        notification = NotificationCreate(
            type="impulse_warning",
            title=title,
            body=body,
            ticker=ticker,
            action=None,
        )
        
        await self._send_to_all(notification)
        return True

    async def _send_to_all(self, notification: NotificationCreate) -> None:
        """
        Send notification to all configured notifiers.
        
        One failure does not block others - each notifier is isolated.
        
        Args:
            notification: The notification to send
        """
        for notifier in self._notifiers:
            try:
                success = await notifier.send(notification)
                if not success:
                    print(
                        f"[NotificationService] {notifier.channel_name} "
                        f"returned False for {notification.title}"
                    )
            except Exception as e:
                # Log but don't re-raise - notifier failures should be isolated
                print(
                    f"[NotificationService] {notifier.channel_name} "
                    f"error: {e}"
                )