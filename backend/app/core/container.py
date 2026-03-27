"""
Manual dependency injection container.
Follows SOLID Dependency Inversion principle without third-party frameworks.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.domain.position.interfaces import PositionRepositoryPort
from app.infra.db.repositories.position_repository import PositionRepository


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

    # Placeholders for future steps:
    # def market_data_adapter(self, market: str) -> MarketDataPort: ...
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
