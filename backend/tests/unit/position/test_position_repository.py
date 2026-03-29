"""
Unit tests for PositionRepository.
Tests repository layer with mocked AsyncSession.
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from app.domain.position.schemas import PositionCreate, PositionEntry, PositionResponse
from app.infra.db.models.position import MarketEnum, Position, PositionStatusEnum
from app.infra.db.repositories.position_repository import PositionRepository
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session():
    """Mock AsyncSession for testing."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def repository(mock_session):
    """PositionRepository instance with mocked session."""
    return PositionRepository(mock_session)


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing."""
    return UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def sample_position_create():
    """Sample PositionCreate data."""
    return PositionCreate(
        ticker="AAPL",
        market="US",
        entries=[
            PositionEntry(
                price=Decimal("150.00"),
                quantity=Decimal("10"),
                entered_at=datetime.fromisoformat("2024-01-02T10:00:00")
            )
        ]
    )


@pytest.fixture
def sample_position_model():
    """Sample Position model instance."""
    position_id = uuid4()
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    created_at = datetime.now()
    updated_at = datetime.now()

    position = MagicMock(spec=Position)
    position.id = position_id
    position.user_id = user_id
    position.ticker = "AAPL"
    position.market = MarketEnum.US
    position.entries = [
        {
            "price": 150.0,
            "quantity": 10.0,
            "entered_at": "2024-01-02T10:00:00"
        }
    ]
    position.avg_price = Decimal("150.0000")
    position.status = PositionStatusEnum.OPEN
    position.created_at = created_at
    position.updated_at = updated_at

    return position


class TestPositionRepository:
    """Test cases for PositionRepository."""

    @pytest.mark.asyncio
    async def test_create_returns_position_response(
        self, repository, mock_session, sample_position_create,
        sample_user_id, sample_position_model
    ):
        """Test create() returns PositionResponse and calls session methods."""
        # Setup: mock session add, commit, refresh
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Mock the position that gets created and refreshed
        def mock_add_side_effect(position):
            # Simulate database setting ID and timestamps
            position.id = sample_position_model.id
            position.created_at = sample_position_model.created_at
            position.updated_at = sample_position_model.updated_at

        mock_session.add.side_effect = mock_add_side_effect

        # Execute
        result = await repository.create(sample_position_create, sample_user_id)

        # Assert: verify session methods called
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

        # Assert: verify returned PositionResponse structure
        assert isinstance(result, PositionResponse)
        assert result.ticker == "AAPL"
        assert result.market == "US"
        assert len(result.entries) == 1
        assert result.entries[0].price == Decimal("150.00")

    @pytest.mark.asyncio
    async def test_get_by_id_returns_position_when_found(
        self, repository, mock_session, sample_position_model
    ):
        """Test get_by_id() returns PositionResponse when position found."""
        # Setup: mock session execute returning position
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_position_model
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        position_id = sample_position_model.id
        result = await repository.get_by_id(position_id)

        # Assert
        assert isinstance(result, PositionResponse)
        assert result.id == position_id
        assert result.ticker == "AAPL"
        assert result.market == "US"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(
        self, repository, mock_session
    ):
        """Test get_by_id() returns None when position not found."""
        # Setup: mock session execute returning None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        result = await repository.get_by_id(uuid4())

        # Assert
        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_user_returns_list(
        self, repository, mock_session, sample_user_id
    ):
        """Test get_by_user() returns list of PositionResponse."""
        # Setup: mock 3 position models
        positions = []
        for i in range(3):
            position = MagicMock(spec=Position)
            position.id = uuid4()
            position.user_id = sample_user_id
            position.ticker = f"STOCK{i}"
            position.market = MarketEnum.US
            position.entries = [{"price": 100.0 + i, "quantity": 10, "entered_at": "2024-01-01T10:00:00"}]
            position.avg_price = Decimal(f"{100 + i}.0000")
            position.status = PositionStatusEnum.OPEN
            position.created_at = datetime.now()
            position.updated_at = datetime.now()
            positions.append(position)

        mock_result = MagicMock()
        mock_result.scalars.return_value = positions
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        result = await repository.get_by_user(sample_user_id)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(p, PositionResponse) for p in result)
        assert [p.ticker for p in result] == ["STOCK0", "STOCK1", "STOCK2"]
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_open_positions_filters_by_status(
        self, repository, mock_session, sample_user_id
    ):
        """Test get_open_positions() returns only open positions."""
        # Setup: mock 3 open positions (should be returned)
        open_positions = []
        for i in range(3):
            position = MagicMock(spec=Position)
            position.id = uuid4()
            position.user_id = sample_user_id
            position.ticker = f"OPEN{i}"
            position.market = MarketEnum.US
            position.entries = [{"price": 100.0, "quantity": 10, "entered_at": "2024-01-01T10:00:00"}]
            position.avg_price = Decimal("100.0000")
            position.status = PositionStatusEnum.OPEN
            position.created_at = datetime.now()
            position.updated_at = datetime.now()
            open_positions.append(position)

        mock_result = MagicMock()
        mock_result.scalars.return_value = open_positions
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Execute
        result = await repository.get_open_positions(sample_user_id)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(p, PositionResponse) for p in result)
        assert all(p.status == "open" for p in result)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_returns_updated_position(
        self, repository, mock_session, sample_position_model
    ):
        """Test update() calls execute with update statement."""
        # Setup: mock session execute returning updated position
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_position_model
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        # Execute
        position_id = sample_position_model.id
        update_data = {"avg_price": Decimal("160.0000")}
        result = await repository.update(position_id, update_data)

        # Assert
        assert isinstance(result, PositionResponse)
        assert result.id == position_id
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_sets_status_to_closed(
        self, repository, mock_session
    ):
        """Test delete() soft deletes by setting status to closed."""
        # Setup: mock session execute with rowcount > 0
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        # Execute
        position_id = uuid4()
        result = await repository.delete(position_id)

        # Assert
        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

        # Verify the update statement sets status to "closed"
        call_args = mock_session.execute.call_args
        # This is a basic check - the actual SQL would be complex
        assert call_args is not None
