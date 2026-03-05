"""team moderation and admin notices

Revision ID: c20260303103000
Revises: c20260302103000
Create Date: 2026-03-03 10:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = 'c20260303103000'
down_revision = 'c20260302103000'
branch_labels = None
depends_on = None


def _has_column(table_name, column_name):
    bind = op.get_bind()
    inspector = inspect(bind)
    return column_name in {c['name'] for c in inspector.get_columns(table_name)}


def upgrade():
    if not _has_column('team', 'is_suspended'):
        op.add_column('team', sa.Column('is_suspended', sa.Boolean(), nullable=False, server_default=server_default=sa.false()))
    if not _has_column('team', 'suspension_reason'):
        op.add_column('team', sa.Column('suspension_reason', sa.Text(), nullable=True))
    if not _has_column('team', 'suspended_at'):
        op.add_column('team', sa.Column('suspended_at', sa.DateTime(), nullable=True))
    if not _has_column('team', 'suspended_by_user_id'):
        op.add_column('team', sa.Column('suspended_by_user_id', sa.Integer(), nullable=True))
    if not _has_column('team', 'admin_notice'):
        op.add_column('team', sa.Column('admin_notice', sa.Text(), nullable=True))
    if not _has_column('team', 'admin_notice_at'):
        op.add_column('team', sa.Column('admin_notice_at', sa.DateTime(), nullable=True))


def downgrade():
    # SQLite-safe no-op downgrade for compatibility.
    pass
