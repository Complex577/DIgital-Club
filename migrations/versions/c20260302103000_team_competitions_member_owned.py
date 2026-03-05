"""team-driven competitions and member-created teams

Revision ID: c20260302103000
Revises: c20260212174500
Create Date: 2026-03-02 10:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = 'c20260302103000'
down_revision = 'c20260212174500'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('team') as batch_op:
        batch_op.add_column(sa.Column('created_by_member_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('total_points', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('is_open', sa.Boolean(), nullable=False, server_default='1'))
        batch_op.create_foreign_key('fk_team_created_by_member_id', 'member', ['created_by_member_id'], ['id'])

    with op.batch_alter_table('team_member') as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=20), nullable=False, server_default='approved'))
        batch_op.add_column(sa.Column('requested_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('approved_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('approved_by_member_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_team_member_approved_by_member_id', 'member', ['approved_by_member_id'], ['id'])

    op.create_table(
        'competition_team_enrollment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('competition_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('leader_member_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('enrolled_at', sa.DateTime(), nullable=True),
        sa.Column('disqualified_reason', sa.Text(), nullable=True),
        sa.Column('disqualified_by', sa.Integer(), nullable=True),
        sa.Column('disqualified_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['competition_id'], ['competition.id']),
        sa.ForeignKeyConstraint(['team_id'], ['team.id']),
        sa.ForeignKeyConstraint(['leader_member_id'], ['member.id']),
        sa.ForeignKeyConstraint(['disqualified_by'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('competition_id', 'team_id', name='_competition_team_enrollment_uc'),
    )

    op.create_table(
        'competition_team_enrollment_member',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('enrollment_id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['enrollment_id'], ['competition_team_enrollment.id']),
        sa.ForeignKeyConstraint(['member_id'], ['member.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('enrollment_id', 'member_id', name='_competition_team_enrollment_member_uc'),
    )

    op.create_table(
        'competition_team_submission',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('competition_id', sa.Integer(), nullable=False),
        sa.Column('enrollment_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('submitted_by_member_id', sa.Integer(), nullable=False),
        sa.Column('submission_type', sa.String(length=20), nullable=False),
        sa.Column('submission_value', sa.String(length=255), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('total_score', sa.Float(), nullable=True),
        sa.Column('bonus_points', sa.Float(), nullable=True),
        sa.Column('final_score', sa.Float(), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('points_awarded', sa.Integer(), nullable=True),
        sa.Column('is_winner', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['competition_id'], ['competition.id']),
        sa.ForeignKeyConstraint(['enrollment_id'], ['competition_team_enrollment.id']),
        sa.ForeignKeyConstraint(['team_id'], ['team.id']),
        sa.ForeignKeyConstraint(['submitted_by_member_id'], ['member.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('competition_id', 'team_id', name='_competition_team_submission_uc'),
    )

    op.create_table(
        'competition_team_score',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('judge_id', sa.Integer(), nullable=False),
        sa.Column('criteria_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['submission_id'], ['competition_team_submission.id']),
        sa.ForeignKeyConstraint(['judge_id'], ['user.id']),
        sa.ForeignKeyConstraint(['criteria_id'], ['competition_criteria.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('submission_id', 'judge_id', 'criteria_id', name='_competition_team_score_uc'),
    )

    op.create_table(
        'team_competition_point',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('competition_id', sa.Integer(), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('awarded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['team.id']),
        sa.ForeignKeyConstraint(['competition_id'], ['competition.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_id', 'competition_id', name='_team_competition_point_uc'),
    )


def downgrade():
    op.drop_table('team_competition_point')
    op.drop_table('competition_team_score')
    op.drop_table('competition_team_submission')
    op.drop_table('competition_team_enrollment_member')
    op.drop_table('competition_team_enrollment')

    with op.batch_alter_table('team_member') as batch_op:
        batch_op.drop_constraint('fk_team_member_approved_by_member_id', type_='foreignkey')
        batch_op.drop_column('approved_by_member_id')
        batch_op.drop_column('approved_at')
        batch_op.drop_column('requested_at')
        batch_op.drop_column('status')

    with op.batch_alter_table('team') as batch_op:
        batch_op.drop_constraint('fk_team_created_by_member_id', type_='foreignkey')
        batch_op.drop_column('is_open')
        batch_op.drop_column('total_points')
        batch_op.drop_column('created_by_member_id')
