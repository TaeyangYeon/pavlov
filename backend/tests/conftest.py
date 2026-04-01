import asyncio
from collections.abc import AsyncGenerator, Generator
from datetime import datetime
from decimal import Decimal
from uuid import UUID

import pytest
import pytest_asyncio
from app.core.config import get_settings
from app.infra.db.base import Base, get_async_session
from app.main import app
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.domain.position.schemas import PositionEntry, PositionResponse

settings = get_settings()

# Use test database URL if available, otherwise modify the main database URL
test_db_url = str(
    settings.DATABASE_TEST_URL
    or str(settings.DATABASE_URL).replace(
        settings.POSTGRES_DB, settings.POSTGRES_TEST_DB
    )
)

# Create test engine
test_engine = create_async_engine(
    test_db_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_test_db() -> AsyncGenerator[None, None]:
    """Set up test database."""
    # Import all models to ensure they are registered with Base.metadata

    # For integration tests, we assume tables are already created by Alembic
    # Check if tables exist before creating them
    async with test_engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'users'
        """))
        tables_exist = result.scalar() > 0

        if not tables_exist:
            # Only create tables if they don't exist (for unit tests)
            await conn.run_sync(Base.metadata.create_all)

    yield

    # Don't drop tables automatically - let Alembic handle schema management
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(setup_test_db: None) -> AsyncGenerator[AsyncSession, None]:
    """Get a test database session."""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.fixture
def override_get_db(db_session: AsyncSession) -> AsyncSession:
    """Override the get_async_session dependency."""
    return db_session


@pytest.fixture
def test_app(override_get_db: AsyncSession) -> FastAPI:
    """Create a test FastAPI app with overridden dependencies."""
    app.dependency_overrides[get_async_session] = lambda: override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """Create a test client."""
    return TestClient(test_app)


@pytest_asyncio.fixture
async def async_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac


# Test data fixtures for PnL Calculator
@pytest.fixture
def sample_position_response() -> PositionResponse:
    """Sample position for testing."""
    entry = PositionEntry(
        price=Decimal("150.00"),
        quantity=Decimal("10"),
        entered_at=datetime(2026, 1, 1, 10, 0)
    )
    return PositionResponse(
        id=UUID("12345678-1234-5678-9012-123456789abc"),
        ticker="AAPL",
        market="US",
        entries=[entry],
        avg_price=Decimal("150.0000"),
        status="open",
        created_at=datetime(2026, 1, 1, 10, 0),
        updated_at=datetime(2026, 1, 1, 10, 0)
    )


@pytest.fixture
def multi_entry_position() -> PositionResponse:
    """Position with multiple entries for testing."""
    entries = [
        PositionEntry(
            price=Decimal("100.00"),
            quantity=Decimal("5"),
            entered_at=datetime(2026, 1, 1, 10, 0)
        ),
        PositionEntry(
            price=Decimal("200.00"),
            quantity=Decimal("5"),
            entered_at=datetime(2026, 1, 2, 10, 0)
        )
    ]
    return PositionResponse(
        id=UUID("12345678-1234-5678-9012-123456789abc"),
        ticker="AAPL",
        market="US",
        entries=entries,
        avg_price=Decimal("150.0000"),  # (100*5 + 200*5) / 10 = 150
        status="open",
        created_at=datetime(2026, 1, 1, 10, 0),
        updated_at=datetime(2026, 1, 2, 10, 0)
    )