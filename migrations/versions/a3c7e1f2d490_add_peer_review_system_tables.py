"""Add peer review system tables

Revision ID: a3c7e1f2d490
Revises: 06b9d2e9cc51
Create Date: 2026-04-15 21:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a3c7e1f2d490"
down_revision: Union[str, Sequence[str], None] = "06b9d2e9cc51"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "practice_tasks",
        sa.Column("task_id", sa.String(length=255), nullable=False),
        sa.Column("cohort_id", sa.String(length=255), nullable=False),
        sa.Column("topic_id", sa.String(length=255), nullable=False),
        sa.Column("creator_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "active", "closed", name="taskstatus"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("task_id"),
    )
    op.create_table(
        "task_submissions",
        sa.Column("submission_id", sa.String(length=255), nullable=False),
        sa.Column("task_id", sa.String(length=255), nullable=False),
        sa.Column("learner_id", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "submitted",
                "in_review",
                "approved",
                "revision_requested",
                name="submissionstatus",
            ),
            nullable=False,
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["task_id"], ["practice_tasks.task_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("submission_id"),
    )
    op.create_table(
        "peer_reviews",
        sa.Column("review_id", sa.String(length=255), nullable=False),
        sa.Column("submission_id", sa.String(length=255), nullable=False),
        sa.Column("reviewer_id", sa.String(length=255), nullable=False),
        sa.Column("task_id", sa.String(length=255), nullable=False),
        sa.Column("cohort_id", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "submitted", name="reviewstatus"),
            nullable=False,
        ),
        sa.Column("overall_feedback", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("review_id"),
    )
    op.create_table(
        "review_scores",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("review_id", sa.String(length=255), nullable=False),
        sa.Column("criterion", sa.String(length=255), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["review_id"], ["peer_reviews.review_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("review_scores")
    op.drop_table("peer_reviews")
    op.drop_table("task_submissions")
    op.drop_table("practice_tasks")
    # Drop PostgreSQL enum types created by this migration
    op.execute("DROP TYPE IF EXISTS reviewstatus")
    op.execute("DROP TYPE IF EXISTS submissionstatus")
    op.execute("DROP TYPE IF EXISTS taskstatus")
