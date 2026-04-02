"""add_backtest_results_table

Revision ID: b5f8e1d2a9c3
Revises: 48507568bca7
Create Date: 2026-04-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b5f8e1d2a9c3'
down_revision: str | Sequence[str] | None = '48507568bca7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create backtest_results table."""
    op.create_table('backtest_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('ticker', sa.String(length=10), nullable=False),
        sa.Column('market', sa.String(length=5), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('initial_capital', sa.DECIMAL(precision=15, scale=4), nullable=False),
        sa.Column('final_capital', sa.DECIMAL(precision=15, scale=4), nullable=False),
        sa.Column('total_return_pct', sa.DECIMAL(precision=10, scale=4), nullable=False),
        sa.Column('max_drawdown_pct', sa.DECIMAL(precision=10, scale=4), nullable=False),
        sa.Column('win_rate', sa.DECIMAL(precision=5, scale=4), nullable=False),
        sa.Column('sharpe_ratio', sa.DECIMAL(precision=8, scale=4), nullable=True),
        sa.Column('total_trades', sa.Integer(), nullable=False),
        sa.Column('parameters_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_backtest_results_ticker'), 'backtest_results', ['ticker'], unique=False)


def downgrade() -> None:
    """Drop backtest_results table."""
    op.drop_index(op.f('ix_backtest_results_ticker'), table_name='backtest_results')
    op.drop_table('backtest_results')