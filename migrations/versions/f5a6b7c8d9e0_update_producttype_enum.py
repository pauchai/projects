"""Update producttype enum: remove consultation, add donation.

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-05-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "f5a6b7c8d9e0"
down_revision = "e4f5a6b7c8d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Migrate any existing 'consultation' rows → 'mentoring'
    conn.execute(sa.text(
        "UPDATE project_products SET product_type = 'mentoring' "
        "WHERE product_type = 'consultation'"
    ))

    # Recreate enum without 'consultation', with 'donation' added.
    # PostgreSQL does not support DROP VALUE — must recreate the type.
    conn.execute(sa.text("ALTER TYPE producttype RENAME TO producttype_old"))
    conn.execute(sa.text(
        "CREATE TYPE producttype AS ENUM "
        "('course', 'mentoring', 'onboarding', 'donation', 'other')"
    ))
    conn.execute(sa.text(
        "ALTER TABLE project_products "
        "ALTER COLUMN product_type TYPE producttype "
        "USING product_type::text::producttype"
    ))
    conn.execute(sa.text("DROP TYPE producttype_old"))


def downgrade() -> None:
    conn = op.get_bind()

    # Revert donation → other, mentoring → consultation
    conn.execute(sa.text(
        "UPDATE project_products SET product_type = 'other' "
        "WHERE product_type = 'donation'"
    ))
    conn.execute(sa.text(
        "UPDATE project_products SET product_type = 'consultation' "
        "WHERE product_type = 'mentoring'"
    ))

    conn.execute(sa.text("ALTER TYPE producttype RENAME TO producttype_old"))
    conn.execute(sa.text(
        "CREATE TYPE producttype AS ENUM "
        "('course', 'consultation', 'mentoring', 'onboarding', 'other')"
    ))
    conn.execute(sa.text(
        "ALTER TABLE project_products "
        "ALTER COLUMN product_type TYPE producttype "
        "USING product_type::text::producttype"
    ))
    conn.execute(sa.text("DROP TYPE producttype_old"))
