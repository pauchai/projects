"""Add partner progression tables

Revision ID: 1am3uqaf61kf
Revises: a3c7e1f2d490
Create Date: 2026-04-15 22:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1am3uqaf61kf"
down_revision: Union[str, Sequence[str], None] = "a3c7e1f2d490"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Topic Experts table
    op.create_table(
        "topic_experts",
        sa.Column("expert_id", sa.String(length=255), nullable=False),
        sa.Column("learner_id", sa.String(length=255), nullable=False),
        sa.Column("topic_id", sa.String(length=255), nullable=False),
        sa.Column("cohort_id", sa.String(length=255), nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("validator_id", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("expert_id"),
    )

    # Helper Metrics table (composite primary key)
    op.create_table(
        "helper_metrics",
        sa.Column("learner_id", sa.String(length=255), nullable=False),
        sa.Column("cohort_id", sa.String(length=255), nullable=False),
        sa.Column("learners_helped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "questions_answered", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("tasks_reviewed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_satisfaction", sa.String(length=10), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("learner_id", "cohort_id"),
    )

    # Module Curators table
    op.create_table(
        "module_curators",
        sa.Column("curator_id", sa.String(length=255), nullable=False),
        sa.Column("learner_id", sa.String(length=255), nullable=False),
        sa.Column("module_id", sa.String(length=255), nullable=False),
        sa.Column("cohort_id", sa.String(length=255), nullable=False),
        sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("promoted_by", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("curator_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("module_curators")
    op.drop_table("helper_metrics")
    op.drop_table("topic_experts")
