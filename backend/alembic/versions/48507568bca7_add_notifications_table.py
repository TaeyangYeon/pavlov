"""add_notifications_table

Revision ID: 48507568bca7
Revises: 9632ae77fe88
Create Date: 2026-03-30 22:43:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '48507568bca7'
down_revision: str | Sequence[str] | None = '9632ae77fe88'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create notifications table."""
    # Create enum type safely
    op.execute("DO $$ BEGIN "
               "CREATE TYPE notification_type_enum AS ENUM ('strategy_change', 'tp_sl_alert', 'impulse_warning', 'system'); "
               "EXCEPTION WHEN duplicate_object THEN null; "
               "END $$;")
    
    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('body', sa.String(length=500), nullable=False),
        sa.Column('ticker', sa.String(length=10), nullable=True),
        sa.Column('action', sa.String(length=20), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_notifications_type'), 'notifications', ['type'], unique=False)
    op.create_index(op.f('ix_notifications_ticker'), 'notifications', ['ticker'], unique=False)
    op.create_index(op.f('ix_notifications_is_read'), 'notifications', ['is_read'], unique=False)
    
    # Convert type column to use enum
    op.execute("ALTER TABLE notifications ALTER COLUMN type TYPE notification_type_enum USING type::notification_type_enum")


def downgrade() -> None:
    """Drop notifications table."""
    op.drop_index(op.f('ix_notifications_is_read'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_ticker'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_type'), table_name='notifications')
    op.drop_table('notifications')
    
    # Drop notification_type_enum using raw SQL
    op.execute("DROP TYPE IF EXISTS notification_type_enum")