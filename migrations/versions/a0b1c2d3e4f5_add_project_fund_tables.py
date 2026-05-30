"""Add project fund tables.

Revision ID: a0b1c2d3e4f5
Revises: f5a6b7c8d9e0
Create Date: 2026-05-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a0b1c2d3e4f5"
down_revision = "f5a6b7c8d9e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project_funds",
        sa.Column("fund_id", sa.String(255), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(255),
            sa.ForeignKey("projects.project_id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("balance", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "fund_transactions",
        sa.Column("transaction_id", sa.String(255), primary_key=True),
        sa.Column(
            "fund_id",
            sa.String(255),
            sa.ForeignKey("project_funds.fund_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("ref_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "fund_distributions",
        sa.Column("distribution_id", sa.String(255), primary_key=True),
        sa.Column(
            "fund_id",
            sa.String(255),
            sa.ForeignKey("project_funds.fund_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("initiated_by", sa.String(255), nullable=False),
        sa.Column("note", sa.Text, nullable=False, server_default=""),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("fund_distributions")
    op.drop_table("fund_transactions")
    op.drop_table("project_funds")
