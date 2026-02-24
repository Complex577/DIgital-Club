"""add criteria visibility control

Revision ID: c20260212174500
Revises: c20260212173000
Create Date: 2026-02-12 17:45:00

"""
from alembic import op
import sqlalchemy as sa


revision = 'c20260212174500'
down_revision = 'c20260212173000'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c['name'] for c in inspector.get_columns('competition_criteria')}
    if 'is_visible_to_members' not in cols:
        op.add_column(
            'competition_criteria',
            sa.Column('is_visible_to_members', sa.Boolean(), nullable=False, server_default=sa.true())
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c['name'] for c in inspector.get_columns('competition_criteria')}
    if 'is_visible_to_members' in cols:
        op.drop_column('competition_criteria', 'is_visible_to_members')
