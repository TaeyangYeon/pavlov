"""
Unit tests for DecisionLogRepository.
Tests database operations for decision logging.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.infra.db.repositories.decision_log_repository import DecisionLogRepository
from app.infra.db.models.decision_log import DecisionLog


@pytest.mark.asyncio
class TestDecisionLogRepository:
    """Test decision log repository operations."""

    async def test_record_decision_saves_to_db(self, db_session):
        """Test that recording a decision saves to database."""
        repo = DecisionLogRepository(db_session)
        user_id = uuid4()

        result = await repo.record(
            user_id=user_id,
            ticker="AAPL",
            action="buy",
            price=Decimal("150.00"),
            quantity=Decimal("10.0"),
            ai_suggested=True,
            notes="Test decision",
        )

        assert result.id is not None
        assert result.ticker == "AAPL"
        assert result.action == "buy"
        assert result.price == Decimal("150.00")
        assert result.quantity == Decimal("10.0")
        assert result.ai_suggested is True
        assert result.notes == "Test decision"
        assert result.created_at is not None

    async def test_get_by_ticker_filters_correctly(self, db_session):
        """Test filtering decisions by ticker."""
        repo = DecisionLogRepository(db_session)
        user_id = uuid4()

        # Create decisions for different tickers
        await repo.record(
            user_id=user_id, ticker="AAPL", action="buy",
            price=Decimal("150"), quantity=Decimal("10"),
            ai_suggested=True
        )
        await repo.record(
            user_id=user_id, ticker="MSFT", action="buy", 
            price=Decimal("300"), quantity=Decimal("5"),
            ai_suggested=True
        )
        await repo.record(
            user_id=user_id, ticker="AAPL", action="sell",
            price=Decimal("155"), quantity=Decimal("10"), 
            ai_suggested=True
        )

        aapl_decisions = await repo.get_by_ticker(user_id, "AAPL")
        msft_decisions = await repo.get_by_ticker(user_id, "MSFT")

        assert len(aapl_decisions) == 2
        assert len(msft_decisions) == 1
        assert all(d.ticker == "AAPL" for d in aapl_decisions)
        assert all(d.ticker == "MSFT" for d in msft_decisions)

    async def test_get_recent_returns_n_items(self, db_session):
        """Test getting recent N decisions."""
        repo = DecisionLogRepository(db_session)
        user_id = uuid4()

        # Create 5 decisions
        for i in range(5):
            await repo.record(
                user_id=user_id,
                ticker=f"TICK{i}",
                action="buy",
                price=Decimal("100"),
                quantity=Decimal("10"),
                ai_suggested=True
            )

        recent_3 = await repo.get_recent(user_id, n=3)
        recent_all = await repo.get_recent(user_id, n=10)

        assert len(recent_3) == 3
        assert len(recent_all) == 5

        # Should be ordered by created_at desc (most recent first)
        for i in range(len(recent_3) - 1):
            assert recent_3[i].created_at >= recent_3[i + 1].created_at

    async def test_count_by_ticker_in_period_accuracy(self, db_session):
        """Test counting trades for ticker in specific period."""
        repo = DecisionLogRepository(db_session)
        user_id = uuid4()
        
        # Create decision record with specific timestamp
        now = datetime.now()
        
        # Mock decisions by manually creating DecisionLog records
        # 3 trades in last 7 days
        for days_ago in [1, 3, 6]:
            decision = DecisionLog(
                user_id=user_id,
                ticker="AAPL", 
                action="buy",
                price=Decimal("150"),
                quantity=Decimal("10"),
                ai_suggested=True,
                created_at=now - timedelta(days=days_ago)
            )
            db_session.add(decision)
            
        # 1 trade 10 days ago (outside 7-day window)
        old_decision = DecisionLog(
            user_id=user_id,
            ticker="AAPL",
            action="sell", 
            price=Decimal("155"),
            quantity=Decimal("10"),
            ai_suggested=True,
            created_at=now - timedelta(days=10)
        )
        db_session.add(old_decision)
        
        # Different ticker within period
        different_ticker = DecisionLog(
            user_id=user_id,
            ticker="MSFT",
            action="buy",
            price=Decimal("300"),
            quantity=Decimal("5"),
            ai_suggested=True,
            created_at=now - timedelta(days=2)
        )
        db_session.add(different_ticker)
        
        await db_session.commit()

        count_7_days = await repo.count_by_ticker_in_period(
            user_id, "AAPL", days=7
        )
        count_15_days = await repo.count_by_ticker_in_period(
            user_id, "AAPL", days=15
        )
        count_msft = await repo.count_by_ticker_in_period(
            user_id, "MSFT", days=7
        )

        assert count_7_days == 3  # Only trades within 7 days
        assert count_15_days == 4  # Include the 10-day old trade
        assert count_msft == 1  # Different ticker