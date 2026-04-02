"""add_ai_cost_usd_to_analysis_log

Revision ID: a1b2c3d4e5f6
Revises: b5f8e1d2a9c3
Create Date: 2026-04-02 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: str | Sequence[str] | None = 'b5f8e1d2a9c3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add ai_cost_usd column to analysis_log table."""
    op.add_column('analysis_log', sa.Column('ai_cost_usd', sa.DECIMAL(precision=8, scale=6), nullable=True))


def downgrade() -> None:
    """Remove ai_cost_usd column from analysis_log table."""
    op.drop_column('analysis_log', 'ai_cost_usd')