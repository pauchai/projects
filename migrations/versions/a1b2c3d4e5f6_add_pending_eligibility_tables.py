"""Add pending eligibility tables

Revision ID: a1b2c3d4e5f6
Revises: 7bc3de4fa512
Create Date: 2026-04-16 13:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "7bc3de4fa512"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create pending_competency_validations and pending_curator_promotions tables."""
    op.create_table(
        "pending_competency_validations",
        sa.Column("pending_id", sa.String(length=255), nullable=False),
        sa.Column("learner_id", sa.String(length=255), nullable=False),
        sa.Column("topic_id", sa.String(length=255), nullable=False),
        sa.Column("cohort_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("pending_id"),
    )
    op.create_index(
        "ix_pending_competency_validations_cohort_id",
        "pending_competency_validations",
        ["cohort_id"],
    )
    op.create_index(
        "ix_pending_competency_validations_learner_id",
        "pending_competency_validations",
        ["learner_id"],
    )

    op.create_table(
        "pending_curator_promotions",
        sa.Column("pending_id", sa.String(length=255), nullable=False),
        sa.Column("learner_id", sa.String(length=255), nullable=False),
        sa.Column("module_id", sa.String(length=255), nullable=False),
        sa.Column("cohort_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("pending_id"),
    )
    op.create_index(
        "ix_pending_curator_promotions_cohort_id",
        "pending_curator_promotions",
        ["cohort_id"],
    )
    op.create_index(
        "ix_pending_curator_promotions_learner_id",
        "pending_curator_promotions",
        ["learner_id"],
    )


def downgrade() -> None:
    """Downgrade schema: drop pending eligibility tables."""
    op.drop_index(
        "ix_pending_curator_promotions_learner_id",
        table_name="pending_curator_promotions",
    )
    op.drop_index(
        "ix_pending_curator_promotions_cohort_id",
        table_name="pending_curator_promotions",
    )
    op.drop_table("pending_curator_promotions")

    op.drop_index(
        "ix_pending_competency_validations_learner_id",
        table_name="pending_competency_validations",
    )
    op.drop_index(
        "ix_pending_competency_validations_cohort_id",
        table_name="pending_competency_validations",
    )
    op.drop_table("pending_competency_validations")
