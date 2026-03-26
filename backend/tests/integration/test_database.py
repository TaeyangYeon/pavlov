import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_db_connection(db_session: AsyncSession) -> None:
    """Test database connection works."""
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1
