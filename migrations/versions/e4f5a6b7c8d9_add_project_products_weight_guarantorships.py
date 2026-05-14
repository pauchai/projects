"""add project_products, membership weight, guarantorships.

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-05-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e4f5a6b7c8d9"
down_revision = "d3e4f5a6b7c8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- product_type enum ---
    product_type_enum = sa.Enum(
        "course", "consultation", "mentoring", "onboarding", "other",
        name="producttype",
    )
    product_type_enum.create(op.get_bind(), checkfirst=True)

    # --- product_visibility enum ---
    product_visibility_enum = sa.Enum(
        "public", "members_only",
        name="productvisibility",
    )
    product_visibility_enum.create(op.get_bind(), checkfirst=True)

    # --- project_products table ---
    op.create_table(
        "project_products",
        sa.Column("product_id", sa.String(255), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(255),
            sa.ForeignKey("projects.project_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("product_type", product_type_enum, nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=True),
        sa.Column(
            "visibility",
            product_visibility_enum,
            nullable=False,
            server_default="public",
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("ref_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # --- membership weight ---
    op.add_column(
        "memberships",
        sa.Column("weight", sa.Float, nullable=False, server_default="0.0"),
    )

    # --- guarantee_status enum ---
    guarantee_status_enum = sa.Enum(
        "active", "revoked",
        name="guaranteestatus",
    )
    guarantee_status_enum.create(op.get_bind(), checkfirst=True)

    # --- guarantorships table ---
    op.create_table(
        "guarantorships",
        sa.Column("guarantee_id", sa.String(255), primary_key=True),
        sa.Column("guarantor_id", sa.String(255), nullable=False),
        sa.Column("guaranteed_id", sa.String(255), nullable=False),
        sa.Column(
            "status",
            guarantee_status_enum,
            nullable=False,
            server_default="active",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("blockchain_tx", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("guarantorships")
    op.drop_column("memberships", "weight")
    op.drop_table("project_products")

    op.execute("DROP TYPE IF EXISTS guaranteestatus")
    op.execute("DROP TYPE IF EXISTS productvisibility")
    op.execute("DROP TYPE IF EXISTS producttype")
