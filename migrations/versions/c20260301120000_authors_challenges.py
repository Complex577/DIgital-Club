"""compatibility placeholder for removed authors/challenges migration

Revision ID: c20260301120000
Revises: c20260212174500
Create Date: 2026-03-01 12:00:00.000000
"""

from alembic import op


revision = "c20260301120000"
down_revision = "c20260212174500"
branch_labels = None
depends_on = None


def upgrade():
    # Intentionally no-op. This revision existed in some environments and was removed.
    # Keeping this placeholder preserves migration continuity.
    pass


def downgrade():
    # Intentionally no-op.
    pass

