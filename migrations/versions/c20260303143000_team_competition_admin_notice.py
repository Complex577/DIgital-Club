"""add admin notice fields to competition team enrollment

Revision ID: c20260303143000
Revises: c20260303103000
Create Date: 2026-03-03 14:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "c20260303143000"
down_revision = "c20260303103000"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("competition_team_enrollment", schema=None) as batch_op:
        batch_op.add_column(sa.Column("admin_notice", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("admin_notice_by", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("admin_notice_at", sa.DateTime(), nullable=True))
        batch_op.create_foreign_key(
            "fk_comp_team_enrollment_admin_notice_by_user",
            "user",
            ["admin_notice_by"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table("competition_team_enrollment", schema=None) as batch_op:
        batch_op.drop_constraint("fk_comp_team_enrollment_admin_notice_by_user", type_="foreignkey")
        batch_op.drop_column("admin_notice_at")
        batch_op.drop_column("admin_notice_by")
        batch_op.drop_column("admin_notice")

