"""
Manual dependency injection container.
Follows SOLID Dependency Inversion principle without third-party frameworks.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.domain.market import MarketDataPort
from app.domain.position.interfaces import PositionRepositoryPort
from app.infra.db.repositories.position_repository import PositionRepository
from app.infra.market.kr_adapter import KRMarketAdapter
from app.infra.market.us_adapter import USMarketAdapter


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
