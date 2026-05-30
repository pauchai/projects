"""add guarantee_requests and zero_circles tables.

Revision ID: j9k0l1m2n3o4
Revises: i8j9k0l1m2n3
Create Date: 2026-05-16
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "j9k0l1m2n3o4"
down_revision = "i8j9k0l1m2n3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "guarantee_requests",
        sa.Column("request_id", sa.String(255), primary_key=True),
        sa.Column("ward_id", sa.String(255), nullable=False),
        sa.Column("guarantor_id", sa.String(255), nullable=False),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "zero_circles",
        sa.Column("circle_id", sa.String(255), primary_key=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("initiated_by", sa.String(255), nullable=False),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="open",
        ),
        sa.Column("deposit_stub", sa.Numeric(14, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "zero_circle_members",
        sa.Column(
            "circle_id",
            sa.String(255),
            sa.ForeignKey("zero_circles.circle_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("circle_id", "user_id"),
    )


def downgrade() -> None:
    op.drop_table("zero_circle_members")
    op.drop_table("zero_circles")
    op.drop_table("guarantee_requests")
