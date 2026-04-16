"""Add commissions table

Revision ID: 7bc3de4fa512
Revises: 4ef6xquy94pz
Create Date: 2026-04-16 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7bc3de4fa512"
down_revision: Union[str, Sequence[str], None] = "4ef6xquy94pz"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create commissions table with indexes."""
    op.create_table(
        "commissions",
        sa.Column("commission_id", sa.String(length=255), nullable=False),
        sa.Column("curator_id", sa.String(length=255), nullable=False),
        sa.Column("cohort_id", sa.String(length=255), nullable=False),
        sa.Column("module_id", sa.String(length=255), nullable=False),
        sa.Column("base_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("bonus_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "RELEASED", name="commissionstatus"),
            nullable=False,
        ),
        sa.Column("earned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("release_eligible_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("commission_id"),
    )
    op.create_index(
        "ix_commissions_curator_id",
        "commissions",
        ["curator_id"],
    )
    op.create_index(
        "ix_commissions_cohort_id",
        "commissions",
        ["cohort_id"],
    )


def downgrade() -> None:
    """Downgrade schema: drop commissions table and its indexes."""
    op.drop_index("ix_commissions_cohort_id", table_name="commissions")
    op.drop_index("ix_commissions_curator_id", table_name="commissions")
    op.drop_table("commissions")
    op.execute("DROP TYPE IF EXISTS commissionstatus")
