"""
FastAPI dependency functions.
Provides dependency injection using FastAPI Depends() pattern.
"""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.container import get_container
from app.domain.position.interfaces import PositionRepositoryPort
from app.domain.position.service import PositionService
from app.domain.strategy.engine import StrategyIntegrationEngine
from app.infra.db.base import AsyncSessionLocal


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields AsyncSession with proper cleanup.

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_position_repository(
    session: AsyncSession = Depends(get_db_session),
) -> PositionRepositoryPort:
    """
    Get PositionRepository dependency.

    Args:
        session: Database session dependency

    Returns:
        PositionRepositoryPort: Position repository interface
    """
    return get_container().position_repository(session)


def get_position_service(
    session: AsyncSession = Depends(get_db_session),
) -> PositionService:
    """
    Get PositionService dependency.

    Args:
        session: Database session dependency

    Returns:
        PositionService: Position service instance
    """
    repository = get_container().position_repository(session)
    return PositionService(repository)


def get_strategy_integration_engine(
    session: AsyncSession = Depends(get_db_session),
) -> StrategyIntegrationEngine:
    """
    Get StrategyIntegrationEngine dependency.

    Args:
        session: Database session dependency

    Returns:
        StrategyIntegrationEngine: Strategy integration engine instance
    """
    return get_container().strategy_integration_engine(session)
