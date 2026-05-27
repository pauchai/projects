"""Add community_invite_codes, drop auth_invite_codes

Migration moves invite code management entirely to the community bounded
context. The old auth_invite_codes table is dropped — all invite code
operations now go through community_invite_codes.

Revision ID: m0n1o2p3q4r5
Revises: l0m1n2o3p4q5
Create Date: 2026-05-27
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "m0n1o2p3q4r5"
down_revision = "l0m1n2o3p4q5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Create community_invite_codes ─────────────────────────────────────────
    op.create_table(
        "community_invite_codes",
        sa.Column("code_id", sa.String(255), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True, index=True),
        sa.Column("community_id", sa.String(255), nullable=False),
        sa.Column("issued_by", sa.String(255), nullable=False),
        sa.Column("max_uses", sa.Integer, nullable=False, server_default="1"),
        sa.Column("uses_left", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("role", sa.String(50), nullable=False, server_default="member"),
    )
    op.create_foreign_key(
        "fk_community_invite_codes_community",
        "community_invite_codes",
        "communities",
        ["community_id"],
        ["community_id"],
        ondelete="CASCADE",
    )

    # ── Drop auth_invite_codes ────────────────────────────────────────────────
    op.drop_table("auth_invite_codes")


def downgrade() -> None:
    # ── Restore auth_invite_codes ─────────────────────────────────────────────
    op.create_table(
        "auth_invite_codes",
        sa.Column("code_id", sa.String(255), primary_key=True),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("issued_by", sa.String(255), nullable=False),
        sa.Column("inviter_id", sa.String(255), nullable=True),
        sa.Column("max_uses", sa.Integer, nullable=False, server_default="1"),
        sa.Column("uses_left", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scope", sa.String(20), nullable=False, server_default="system"),
        sa.Column("project_id", sa.String(255), nullable=True),
        sa.Column("community_id", sa.String(255), nullable=True),
        sa.Column("role", sa.String(50), nullable=True),
    )

    # ── Re-create index that was originally created in b1c2d3e4f5a6 ──
    op.create_index(
        "ix_auth_invite_codes_code", "auth_invite_codes", ["code"], unique=True
    )

    # ── Re-create FK on auth_invite_codes that existed before l0m1n2o3p4q5 ──
    op.create_foreign_key(
        "fk_invite_codes_community",
        "auth_invite_codes", "communities",
        ["community_id"], ["community_id"],
        ondelete="CASCADE",
    )

    # ── Drop community_invite_codes ───────────────────────────────────────────
    op.drop_constraint(
        "fk_community_invite_codes_community",
        "community_invite_codes",
        type_="foreignkey",
    )
    op.drop_table("community_invite_codes")
