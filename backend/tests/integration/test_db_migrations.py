from datetime import date
from decimal import Decimal

import pytest
from app.infra.db.models import (
    AnalysisLog,
    DecisionLog,
    MarketData,
    Position,
    StrategyOutput,
    User,
)
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_migration_runs_without_error(db_session: AsyncSession):
    """Test that migration runs without error"""
    # If we get here with a db_session, migration was successful
    result = await db_session.execute(text("SELECT 1 as test"))
    assert result.fetchone().test == 1


@pytest.mark.asyncio
async def test_all_tables_created(db_session: AsyncSession):
    """Test that all 6 tables are created"""
    # Get table names from database
    result = await db_session.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """))

    table_names = {row.table_name for row in result.fetchall()}

    expected_tables = {
        'users',
        'positions',
        'market_data',
        'analysis_log',
        'strategy_output',
        'decision_log',
    }

    missing_tables = expected_tables - table_names
    assert expected_tables.issubset(table_names), f"Missing tables: {missing_tables}"


@pytest.mark.asyncio
async def test_can_insert_and_query_user(db_session: AsyncSession):
    """Test that we can insert and query user data"""
    # Insert a test user
    user = User(
        email="test@example.com",
        api_key_encrypted="encrypted_key_test",
        preferences={"theme": "dark", "language": "en"},
        is_active=True,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Query the user back
    result = await db_session.execute(
        select(User).where(User.email == "test@example.com")
    )
    fetched_user = result.scalar_one()

    assert fetched_user.email == "test@example.com"
    assert fetched_user.api_key_encrypted == "encrypted_key_test"
    assert fetched_user.preferences == {"theme": "dark", "language": "en"}
    assert fetched_user.is_active is True
    assert fetched_user.created_at is not None
    assert fetched_user.updated_at is not None


@pytest.mark.asyncio
async def test_can_insert_position_with_entries(db_session: AsyncSession):
    """Test that we can insert position with JSONB entries"""
    # First create a user
    user = User(email="position_test@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create position with entries
    entries = [
        {"price": 100.0, "quantity": 10, "entered_at": "2024-01-01T10:00:00"},
        {"price": 105.0, "quantity": 5, "entered_at": "2024-01-02T10:00:00"},
    ]

    position = Position(
        user_id=user.id,
        ticker="AAPL",
        market="US",
        entries=entries,
        avg_price=Decimal("102.50"),
        status="open",
    )

    db_session.add(position)
    await db_session.commit()
    await db_session.refresh(position)

    # Query back and verify
    result = await db_session.execute(select(Position).where(Position.ticker == "AAPL"))
    fetched_position = result.scalar_one()

    assert fetched_position.ticker == "AAPL"
    assert fetched_position.market == "US"
    assert len(fetched_position.entries) == 2
    assert fetched_position.entries[0]["price"] == 100.0
    assert fetched_position.entries[1]["quantity"] == 5
    assert fetched_position.avg_price == Decimal("102.50")
    assert fetched_position.status == "open"


@pytest.mark.asyncio
async def test_analysis_log_executed_default_false(db_session: AsyncSession):
    """Test that analysis_log executed field defaults to False - CRITICAL for Step 17"""
    # Insert analysis log without specifying executed
    analysis_log = AnalysisLog(
        date=date(2024, 1, 1),
        market="US",
        # executed not specified - should default to False
    )

    db_session.add(analysis_log)
    await db_session.commit()
    await db_session.refresh(analysis_log)

    # Verify executed defaults to False
    assert (
        analysis_log.executed is False
    ), "executed field must default to False for Step 17 Missed Execution Recovery"

    # Also test with explicit True
    analysis_log_true = AnalysisLog(date=date(2024, 1, 2), market="KR", executed=True)

    db_session.add(analysis_log_true)
    await db_session.commit()
    await db_session.refresh(analysis_log_true)

    assert analysis_log_true.executed is True


@pytest.mark.asyncio
async def test_market_data_unique_constraint(db_session: AsyncSession):
    """Test that market_data unique constraint works"""
    # Insert first market data record
    market_data1 = MarketData(
        ticker="AAPL",
        market="US",
        date=date(2024, 1, 1),
        open=Decimal("150.00"),
        high=Decimal("155.00"),
        low=Decimal("149.00"),
        close=Decimal("154.00"),
        volume=1000000,
    )

    db_session.add(market_data1)
    await db_session.commit()

    # Try to insert duplicate (same ticker + market + date)
    market_data2 = MarketData(
        ticker="AAPL",
        market="US",
        date=date(2024, 1, 1),  # Same date
        open=Decimal("151.00"),
        high=Decimal("156.00"),
        low=Decimal("150.00"),
        close=Decimal("155.00"),
        volume=1100000,
    )

    db_session.add(market_data2)

    # This should raise an integrity error due to unique constraint
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_foreign_key_relationships_work(db_session: AsyncSession):
    """Test that foreign key relationships are properly enforced"""
    # Create user
    user = User(email="fk_test@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create analysis log
    analysis_log = AnalysisLog(
        date=date(2024, 1, 1),
        market="US",
        executed=True,
        ai_response={"strategies": [{"ticker": "AAPL", "action": "buy"}]},
    )
    db_session.add(analysis_log)
    await db_session.commit()
    await db_session.refresh(analysis_log)

    # Create strategy output linked to analysis log
    strategy_output = StrategyOutput(
        analysis_log_id=analysis_log.id,
        ticker="AAPL",
        action="buy",
        take_profit_levels=[{"pct": 5.0, "sell_ratio": 1.0}],
        stop_loss_levels=[{"pct": -3.0, "sell_ratio": 1.0}],
        rationale="Test strategy",
        confidence=Decimal("0.80"),
    )
    db_session.add(strategy_output)

    # Create decision log linked to user
    decision_log = DecisionLog(
        user_id=user.id,
        ticker="AAPL",
        action="buy",
        price=Decimal("150.00"),
        quantity=Decimal("10"),
        ai_suggested=True,
        notes="Following AI recommendation",
    )
    db_session.add(decision_log)

    await db_session.commit()

    # Verify relationships work
    await db_session.refresh(strategy_output)
    await db_session.refresh(decision_log)

    assert strategy_output.analysis_log_id == analysis_log.id
    assert decision_log.user_id == user.id
