"""Add reward_ledger table

Revision ID: 4ef6xquy94pz
Revises: 1am3uqaf61kf
Create Date: 2026-04-16 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4ef6xquy94pz"
down_revision: Union[str, Sequence[str], None] = "1am3uqaf61kf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create reward_ledger table with indexes."""
    op.create_table(
        "reward_ledger",
        sa.Column("entry_id", sa.String(length=255), nullable=False),
        sa.Column("learner_id", sa.String(length=255), nullable=False),
        sa.Column("reward_type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("triggering_event", sa.String(length=255), nullable=True),
        sa.Column("cohort_id", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("entry_id"),
    )
    op.create_index(
        "ix_reward_ledger_learner_id",
        "reward_ledger",
        ["learner_id"],
    )
    op.create_index(
        "ix_reward_ledger_reward_type",
        "reward_ledger",
        ["reward_type"],
    )


def downgrade() -> None:
    """Downgrade schema: drop reward_ledger table and its indexes."""
    op.drop_index("ix_reward_ledger_reward_type", table_name="reward_ledger")
    op.drop_index("ix_reward_ledger_learner_id", table_name="reward_ledger")
    op.drop_table("reward_ledger")
