"""Add invite_codes table and inviter_id to auth_users

Revision ID: b1c2d3e4f5a6
Revises: a3c7e1f2d490
Create Date: 2026-04-18 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "1afcb6cfa500"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add invite_codes table
    op.create_table(
        "auth_invite_codes",
        sa.Column("code_id", sa.String(255), primary_key=True),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("issued_by", sa.String(255), nullable=False),
        sa.Column(
            "inviter_id",
            sa.String(255),
            sa.ForeignKey("auth_users.user_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("max_uses", sa.Integer, nullable=False, default=1),
        sa.Column("uses_left", sa.Integer, nullable=False, default=1),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_auth_invite_codes_code", "auth_invite_codes", ["code"], unique=True
    )

    # 2. Add inviter_id to auth_users (nullable FK — seed users have no inviter)
    op.add_column(
        "auth_users",
        sa.Column(
            "inviter_id",
            sa.String(255),
            sa.ForeignKey("auth_users.user_id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("auth_users", "inviter_id")
    op.drop_index("ix_auth_invite_codes_code", table_name="auth_invite_codes")
    op.drop_table("auth_invite_codes")
