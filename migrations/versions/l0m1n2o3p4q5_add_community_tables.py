"""Add community tables: communities, memberships, funds, feature_requests

Revision ID: l0m1n2o3p4q5
Revises: k0l1m2n3o4p5
Create Date: 2026-05-27
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "l0m1n2o3p4q5"
down_revision = "k0l1m2n3o4p5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── communities ──────────────────────────────────────────────────────────
    op.create_table(
        "communities",
        sa.Column("community_id", sa.String(255), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("owner_id", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.Text, nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "suspended", "archived", name="communitystatus"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── community_memberships ────────────────────────────────────────────────
    op.create_table(
        "community_memberships",
        sa.Column("membership_id", sa.String(255), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("community_id", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("owner", "admin", "moderator", "member", name="communityrole"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("weight", sa.Float, nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(
            ["community_id"],
            ["communities.community_id"],
            ondelete="CASCADE",
        ),
    )

    # ── community_funds ──────────────────────────────────────────────────────
    op.create_table(
        "community_funds",
        sa.Column("fund_id", sa.String(255), primary_key=True),
        sa.Column("community_id", sa.String(255), nullable=False, unique=True),
        sa.Column(
            "balance", sa.Numeric(14, 2), nullable=False, server_default="0"
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["community_id"],
            ["communities.community_id"],
            ondelete="CASCADE",
        ),
    )

    # ── community_fund_transactions ───────────────────────────────────────────
    op.create_table(
        "community_fund_transactions",
        sa.Column("transaction_id", sa.String(255), primary_key=True),
        sa.Column("fund_id", sa.String(255), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("ref_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["fund_id"],
            ["community_funds.fund_id"],
            ondelete="CASCADE",
        ),
    )

    # ── community_fund_distributions ──────────────────────────────────────────
    op.create_table(
        "community_fund_distributions",
        sa.Column("distribution_id", sa.String(255), primary_key=True),
        sa.Column("fund_id", sa.String(255), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("initiated_by", sa.String(255), nullable=False),
        sa.Column("note", sa.Text, nullable=False, server_default=""),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["fund_id"],
            ["community_funds.fund_id"],
            ondelete="CASCADE",
        ),
    )

    # ── auth_invite_codes: add community_id ──────────────────────────────────
    op.add_column(
        "auth_invite_codes",
        sa.Column("community_id", sa.String(255), nullable=True),
    )
    op.create_foreign_key(
        "fk_invite_codes_community",
        "auth_invite_codes", "communities",
        ["community_id"], ["community_id"],
        ondelete="CASCADE",
    )

    # ── community_feature_requests ───────────────────────────────────────────
    op.create_table(
        "community_feature_requests",
        sa.Column("request_id", sa.String(255), primary_key=True),
        sa.Column("community_id", sa.String(255), nullable=False),
        sa.Column("author_id", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column(
            "status",
            sa.Enum(
                "submitted", "planned", "in_progress", "done", "rejected",
                name="featurestatus",
            ),
            nullable=False,
            server_default="submitted",
        ),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("priority", sa.String(50), nullable=True),
        sa.Column("admin_notes", sa.Text, nullable=True, server_default=""),
        sa.Column("metadata", JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["community_id"],
            ["communities.community_id"],
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    op.drop_constraint("fk_invite_codes_community", "auth_invite_codes", type_="foreignkey")
    op.drop_column("auth_invite_codes", "community_id")
    op.drop_table("community_feature_requests")
    op.drop_table("community_fund_distributions")
    op.drop_table("community_fund_transactions")
    op.drop_table("community_funds")
    op.drop_table("community_memberships")
    op.drop_table("communities")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS featurestatus")
    op.execute("DROP TYPE IF EXISTS communityrole")
    op.execute("DROP TYPE IF EXISTS communitystatus")
