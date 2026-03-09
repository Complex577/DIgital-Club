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
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_name = "competition_team_enrollment"

    if table_name not in inspector.get_table_names():
        return

    existing_columns = {col["name"] for col in inspector.get_columns(table_name)}

    if "admin_notice" not in existing_columns:
        op.add_column(table_name, sa.Column("admin_notice", sa.Text(), nullable=True))
    if "admin_notice_by" not in existing_columns:
        op.add_column(table_name, sa.Column("admin_notice_by", sa.Integer(), nullable=True))
    if "admin_notice_at" not in existing_columns:
        op.add_column(table_name, sa.Column("admin_notice_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("competition_team_enrollment", schema=None) as batch_op:
        batch_op.drop_constraint("fk_comp_team_enrollment_admin_notice_by_user", type_="foreignkey")
        batch_op.drop_column("admin_notice_at")
        batch_op.drop_column("admin_notice_by")
        batch_op.drop_column("admin_notice")
