"""
Unit tests for Container dependency injection.
"""

from unittest.mock import MagicMock

import pytest
from app.core.config import Settings
from app.core.container import Container, get_container
from app.domain.market.service import MarketDataService
from app.infra.db.repositories.market_data_repository import MarketDataRepository


class TestContainer:
    """Test dependency injection container."""

    @pytest.fixture
    def settings(self):
        """Mock settings for testing."""
        return Settings(
            SECRET_KEY="test-key",
            DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test",
            DATABASE_TEST_URL="postgresql+asyncpg://test:test@localhost:5433/test",
            POSTGRES_USER="test",
            POSTGRES_PASSWORD="test",
            POSTGRES_DB="test",
            POSTGRES_TEST_DB="test",
        )

    @pytest.fixture
    def container(self, settings):
        """Container instance for testing."""
        return Container(settings)

    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        return MagicMock()

    def test_market_data_repository_creation(self, container, mock_session):
        """Test MarketDataRepository factory method."""
        repository = container.market_data_repository(mock_session)
        assert isinstance(repository, MarketDataRepository)
        assert repository._session is mock_session

    def test_market_data_service_creation_kr(self, container, mock_session):
        """Test MarketDataService factory method for KR market."""
        service = container.market_data_service("KR", mock_session)
        assert isinstance(service, MarketDataService)
        assert isinstance(service._repository, MarketDataRepository)

    def test_market_data_service_creation_us(self, container, mock_session):
        """Test MarketDataService factory method for US market."""
        service = container.market_data_service("US", mock_session)
        assert isinstance(service, MarketDataService)
        assert isinstance(service._repository, MarketDataRepository)

    def test_market_data_service_invalid_market(self, container, mock_session):
        """Test MarketDataService with invalid market raises error."""
        with pytest.raises(ValueError, match="Unsupported market: INVALID"):
            container.market_data_service("INVALID", mock_session)

    def test_get_container_singleton(self):
        """Test get_container returns singleton instance."""
        container1 = get_container()
        container2 = get_container()
        assert container1 is container2
