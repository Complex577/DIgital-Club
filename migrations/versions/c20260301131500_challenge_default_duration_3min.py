"""compatibility placeholder for removed challenge duration migration

Revision ID: c20260301131500
Revises: c20260301120000
Create Date: 2026-03-01 13:15:00.000000
"""


revision = "c20260301131500"
down_revision = "c20260301120000"
branch_labels = None
depends_on = None


def upgrade():
    # Intentionally no-op.
    # Keeps migration chain compatible with environments that were stamped
    # with this revision before challenge features were removed.
    pass


def downgrade():
    # Intentionally no-op.
    pass
