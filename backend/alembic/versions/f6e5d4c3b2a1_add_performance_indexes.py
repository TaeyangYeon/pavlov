"""add_performance_indexes

Revision ID: f6e5d4c3b2a1
Revises: a1b2c3d4e5f6
Create Date: 2026-04-02 00:01:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f6e5d4c3b2a1'
down_revision: str | Sequence[str] | None = 'a1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add performance indexes for query optimization."""
    # analysis_log compound index
    op.create_index(
        "ix_analysis_log_market_date_executed",
        "analysis_log",
        ["market", "date", "executed"],
        unique=False,
        postgresql_using="btree",
    )
    # positions compound index
    op.create_index(
        "ix_positions_user_id_status",
        "positions",
        ["user_id", "status"],
        unique=False,
    )
    # notifications compound index
    op.create_index(
        "ix_notifications_is_read_created_at",
        "notifications",
        ["is_read", "created_at"],
        unique=False,
    )
    # decision_log compound index
    op.create_index(
        "ix_decision_log_user_ticker_created",
        "decision_log",
        ["user_id", "ticker", "created_at"],
        unique=False,
    )
    # strategy_output compound index
    op.create_index(
        "ix_strategy_output_ticker_created",
        "strategy_output",
        ["ticker", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index("ix_strategy_output_ticker_created")
    op.drop_index("ix_decision_log_user_ticker_created")
    op.drop_index("ix_notifications_is_read_created_at")
    op.drop_index("ix_positions_user_id_status")
    op.drop_index("ix_analysis_log_market_date_executed")