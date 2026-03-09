"""add quiz management and exam system tables

Revision ID: c20260305113000
Revises: c20260303143000
Create Date: 2026-03-05 11:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "c20260305113000"
down_revision = "c20260303143000"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "quiz",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("field_of_study", sa.String(length=80), nullable=False),
        sa.Column("topic", sa.String(length=200), nullable=False),
        sa.Column("generation_meta_json", sa.Text(), nullable=True),
        sa.Column("total_questions", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("mcq_count", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("tf_count", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("visibility", sa.String(length=20), nullable=False, server_default="members"),
        sa.Column("provider_used", sa.String(length=30), nullable=True),
        sa.Column("provider_job_id", sa.String(length=120), nullable=True),
        sa.Column("generation_error", sa.Text(), nullable=True),
        sa.Column("generation_started_at", sa.DateTime(), nullable=True),
        sa.Column("generation_completed_at", sa.DateTime(), nullable=True),
        sa.Column("submitted_for_approval_at", sa.DateTime(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("scheduled_start_at", sa.DateTime(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "quiz_resource",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quiz_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=True),
        sa.Column("file_path", sa.String(length=255), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["quiz_id"], ["quiz.id"]),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "quiz_question",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quiz_id", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("question_type", sa.String(length=20), nullable=False),
        sa.Column("scenario", sa.Text(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("difficulty", sa.String(length=20), nullable=True, server_default="medium"),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["quiz_id"], ["quiz.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quiz_id", "order_index", name="uq_quiz_question_order"),
    )

    op.create_table(
        "quiz_option",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("option_key", sa.String(length=8), nullable=False),
        sa.Column("option_text", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["question_id"], ["quiz_question.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("question_id", "option_key", name="uq_quiz_option_key"),
    )

    op.create_table(
        "quiz_attempt",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quiz_id", sa.Integer(), nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="in_progress"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True, server_default="0"),
        sa.Column("correct_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("total_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("violation_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("tab_switch_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("blur_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("paste_attempt_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("inactivity_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("confidence_factor", sa.Float(), nullable=True, server_default="1"),
        sa.Column("confidence_adjusted_score", sa.Float(), nullable=True, server_default="0"),
        sa.Column("auto_submit_reason", sa.String(length=80), nullable=True),
        sa.Column("random_seed", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["member_id"], ["member.id"]),
        sa.ForeignKeyConstraint(["quiz_id"], ["quiz.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quiz_id", "member_id", name="uq_quiz_member_attempt"),
    )

    op.create_table(
        "quiz_attempt_answer",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("selected_option_id", sa.Integer(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True, server_default=sa.text("0")),
        sa.Column("time_spent_seconds", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["attempt_id"], ["quiz_attempt.id"]),
        sa.ForeignKeyConstraint(["question_id"], ["quiz_question.id"]),
        sa.ForeignKeyConstraint(["selected_option_id"], ["quiz_option.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question_answer"),
    )

    op.create_table(
        "quiz_violation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("violation_type", sa.String(length=30), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["attempt_id"], ["quiz_attempt.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "quiz_leaderboard",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quiz_id", sa.Integer(), nullable=False),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("points_awarded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["attempt_id"], ["quiz_attempt.id"]),
        sa.ForeignKeyConstraint(["member_id"], ["member.id"]),
        sa.ForeignKeyConstraint(["quiz_id"], ["quiz.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id"),
        sa.UniqueConstraint("quiz_id", "member_id", name="uq_quiz_member_leaderboard"),
        sa.UniqueConstraint("quiz_id", "rank", name="uq_quiz_rank"),
    )


def downgrade():
    op.drop_table("quiz_leaderboard")
    op.drop_table("quiz_violation")
    op.drop_table("quiz_attempt_answer")
    op.drop_table("quiz_attempt")
    op.drop_table("quiz_option")
    op.drop_table("quiz_question")
    op.drop_table("quiz_resource")
    op.drop_table("quiz")

