"""add project_products, membership weight.

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-05-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e4f5a6b7c8d9"
down_revision = "d3e4f5a6b7c8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # --- enums (idempotent via DO block) ---
    conn.execute(sa.text(
        "DO $$ BEGIN "
        "  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'producttype') THEN "
        "    CREATE TYPE producttype AS ENUM ('course', 'consultation', 'mentoring', 'onboarding', 'other'); "
        "  END IF; "
        "END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN "
        "  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'productvisibility') THEN "
        "    CREATE TYPE productvisibility AS ENUM ('public', 'members_only'); "
        "  END IF; "
        "END $$"
    ))

    # Enum column references — postgresql.ENUM with create_type=False so
    # SQLAlchemy never emits CREATE TYPE (we already did that above).
    product_type_col = postgresql.ENUM(
        "course", "consultation", "mentoring", "onboarding", "other",
        name="producttype", create_type=False,
    )
    product_visibility_col = postgresql.ENUM(
        "public", "members_only",
        name="productvisibility", create_type=False,
    )

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
        sa.Column("product_type", product_type_col, nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=True),
        sa.Column(
            "visibility",
            product_visibility_col,
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


def downgrade() -> None:
    op.drop_column("memberships", "weight")
    op.drop_table("project_products")

    op.execute("DROP TYPE IF EXISTS productvisibility")
    op.execute("DROP TYPE IF EXISTS producttype")
