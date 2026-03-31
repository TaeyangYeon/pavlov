"""
Manual dependency injection container.
Follows SOLID Dependency Inversion principle without third-party frameworks.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.domain.ai.anthropic_client import AnthropicClient
from app.domain.ai.client import AIClient
from app.domain.ai.pipeline import AnalysisPipeline
from app.domain.filter.chain import FilterChain, build_default_filter_chain
from app.domain.indicator.engine import IndicatorEngine
from app.domain.market import MarketDataPort
from app.domain.market.service import MarketDataService
from app.domain.position.interfaces import PositionRepositoryPort
from app.domain.position.service import PositionService
from app.domain.strategy.change_detector import ChangeDetector
from app.domain.strategy.engine import StrategyIntegrationEngine
from app.infra.db.repositories.analysis_log_repository import AnalysisLogRepository
from app.infra.db.repositories.market_data_repository import MarketDataRepository
from app.infra.db.repositories.position_repository import PositionRepository
from app.infra.db.repositories.strategy_output_repository import StrategyOutputRepository
from app.infra.market.kr_adapter import KRMarketAdapter
from app.infra.market.us_adapter import USMarketAdapter
from app.domain.notification.interfaces import NotificationPort
from app.domain.notification.service import NotificationService
from app.infra.db.repositories.notification_repository import NotificationRepository
from app.infra.notification.email_notifier import EmailNotifier
from app.infra.notification.in_app_notifier import InAppNotifier
from app.infra.crypto.encryption import EncryptionService
from app.domain.user.service import UserService
from app.infra.db.repositories.user_repository import UserRepository


class Container:
    """
    Manual dependency injection container.
    Holds factory methods for all domain services.
    No third-party DI framework used (SOLID D principle).
    """

    def __init__(self, settings: Settings):
        self._settings = settings

    def position_repository(self, session: AsyncSession) -> PositionRepositoryPort:
        """
        Create PositionRepository instance.

        Args:
            session: Database session

        Returns:
            PositionRepositoryPort implementation
        """
        return PositionRepository(session)

    def kr_market_adapter(self) -> MarketDataPort:
        """
        Create KRMarketAdapter instance.

        Returns:
            MarketDataPort implementation for Korean market
        """
        return KRMarketAdapter()

    def us_market_adapter(self) -> MarketDataPort:
        """
        Create USMarketAdapter instance.

        Returns:
            MarketDataPort implementation for US market
        """
        return USMarketAdapter()

    def market_adapter(self, market: str) -> MarketDataPort:
        """
        Return appropriate adapter based on market string.

        Args:
            market: Market identifier ("KR" or "US")

        Returns:
            MarketDataPort implementation for the specified market

        Raises:
            ValueError: If market identifier is not supported
        """
        if market == "KR":
            return self.kr_market_adapter()
        elif market == "US":
            return self.us_market_adapter()
        else:
            raise ValueError(f"Unsupported market: {market}")

    def market_data_repository(self, session: AsyncSession) -> MarketDataRepository:
        """
        Create MarketDataRepository instance.

        Args:
            session: Database session

        Returns:
            MarketDataRepository implementation
        """
        return MarketDataRepository(session)

    def market_data_service(
        self, market: str, session: AsyncSession
    ) -> MarketDataService:
        """
        Create MarketDataService instance with cache-aside pattern.

        Args:
            market: Market identifier ("KR" or "US")
            session: Database session

        Returns:
            MarketDataService implementation

        Raises:
            ValueError: If market identifier is not supported
        """
        adapter = self.market_adapter(market)
        repository = self.market_data_repository(session)
        return MarketDataService(adapter, repository)

    def indicator_engine(self) -> IndicatorEngine:
        """
        Create IndicatorEngine instance.

        Returns:
            IndicatorEngine implementation
        """
        return IndicatorEngine()

    def filter_chain(self) -> FilterChain:
        """
        Create FilterChain instance with default filters.

        Returns:
            FilterChain with VolumeFilter, VolatilityFilter, MAAlignmentFilter
        """
        return build_default_filter_chain()

    def encryption_service(self) -> EncryptionService:
        key = self._settings.ENCRYPTION_KEY
        return EncryptionService(key=key)

    def user_repository(
        self, session: AsyncSession
    ) -> UserRepository:
        return UserRepository(
            session=session,
            encryption=self.encryption_service(),
        )

    def user_service(
        self, session: AsyncSession
    ) -> UserService:
        return UserService(
            repository=self.user_repository(session),
            settings=self._settings,
        )

    def ai_client(
        self,
        session: AsyncSession | None = None,
        user_id: "UUID | None" = None,
    ) -> AIClient:
        """
        Priority:
        1. DB user api_key (if session + user_id provided)
        2. ANTHROPIC_API_KEY from settings
        3. MockAIClient fallback
        """
        # Try DB key first - this is sync context, so we store
        # the DB key retrieval for async callers
        # Full async implementation via get_ai_client_for_user
        
        # Env key fallback
        api_key = self._settings.ANTHROPIC_API_KEY
        if api_key:
            return AnthropicClient(api_key=api_key)

        # Mock fallback for development
        from app.domain.ai.client import MockAIClient
        return MockAIClient()

    async def get_ai_client_for_user(
        self,
        session: AsyncSession,
        user_id: "UUID",
    ) -> AIClient:
        """
        Async method to get AI client with DB key lookup.
        Used by scheduler jobs and analysis pipeline.
        """
        from uuid import UUID
        user_repo = self.user_repository(session)
        db_key = await user_repo.get_api_key(user_id)

        if db_key:
            return AnthropicClient(api_key=db_key)

        # Fallback to env key
        env_key = self._settings.ANTHROPIC_API_KEY
        if env_key:
            return AnthropicClient(api_key=env_key)

        from app.domain.ai.client import MockAIClient
        return MockAIClient()

    def analysis_log_repository(self, session: AsyncSession) -> AnalysisLogRepository:
        """
        Create AnalysisLogRepository instance.

        Args:
            session: Database session

        Returns:
            AnalysisLogRepository implementation
        """
        return AnalysisLogRepository(session)

    def analysis_pipeline(self, session: AsyncSession) -> AnalysisPipeline:
        """
        Create AnalysisPipeline instance with dependencies.

        Args:
            session: Database session

        Returns:
            AnalysisPipeline implementation
        """
        ai_client = self.ai_client()
        log_repository = self.analysis_log_repository(session)
        return AnalysisPipeline(ai_client, log_repository)

    def position_service(self, session: AsyncSession) -> PositionService:
        """
        Create PositionService instance with dependencies.

        Args:
            session: Database session

        Returns:
            PositionService implementation
        """
        position_repository = self.position_repository(session)
        return PositionService(position_repository)

    def strategy_output_repository(self, session: AsyncSession) -> StrategyOutputRepository:
        """
        Create StrategyOutputRepository instance.

        Args:
            session: Database session

        Returns:
            StrategyOutputRepository implementation
        """
        return StrategyOutputRepository(session)

    def change_detector(self) -> ChangeDetector:
        """
        Create ChangeDetector instance.

        Returns:
            ChangeDetector implementation
        """
        return ChangeDetector()

    def strategy_integration_engine(self, session: AsyncSession) -> StrategyIntegrationEngine:
        """
        Create StrategyIntegrationEngine instance with dependencies.

        Args:
            session: Database session

        Returns:
            StrategyIntegrationEngine implementation
        """
        position_service = self.position_service(session)
        strategy_repository = self.strategy_output_repository(session)
        change_detector = self.change_detector()
        return StrategyIntegrationEngine(
            position_service, strategy_repository, change_detector
        )

    def notification_repository(self, session: AsyncSession) -> NotificationRepository:
        """
        Create NotificationRepository instance.

        Args:
            session: Database session

        Returns:
            NotificationRepository implementation
        """
        return NotificationRepository(session)

    def notification_service(self, session: AsyncSession) -> NotificationService:
        """
        Create NotificationService with all configured notifiers.

        Args:
            session: Database session for repository operations

        Returns:
            NotificationService: Configured notification service
        """
        repo = self.notification_repository(session)

        # Always include in-app notifications
        notifiers: list[NotificationPort] = [
            InAppNotifier(repo),
        ]

        # Optionally include email notifications
        if self._settings.email_enabled:
            notifiers.append(EmailNotifier(self._settings))

        return NotificationService(
            notifiers=notifiers,
            repository=repo,
            settings=self._settings,
        )

    # Placeholders for future steps:
    # def strategy_service(self, session) -> StrategyPort: ...


# Global container instance
_container: Container | None = None


def get_container() -> Container:
    """
    Get global dependency injection container.

    Returns:
        Container instance
    """
    global _container
    if _container is None:
        _container = Container(settings=get_settings())
    return _container
