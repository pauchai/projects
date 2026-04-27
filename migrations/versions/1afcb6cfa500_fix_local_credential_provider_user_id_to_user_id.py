"""Fix local credential provider_user_id: store user_id instead of email.

For local (email+password) credentials, provider_user_id previously stored the
user's email address, duplicating the email that already lives on the users table.
This migration updates all existing local credentials to store user_id instead.

Revision ID: 1afcb6cfa500
Revises: a1b2c3d4e5f6
Create Date: 2026-04-18 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1afcb6cfa500"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Set provider_user_id = user_id for all local credentials."""
    op.execute(
        """
        UPDATE auth_credentials
        SET provider_user_id = user_id
        WHERE provider = 'local'
        """
    )


def downgrade() -> None:
    """Restore provider_user_id = email for local credentials (from users table)."""
    op.execute(
        """
        UPDATE auth_credentials
        SET provider_user_id = u.email
        FROM auth_users u
        WHERE auth_credentials.user_id = u.user_id
          AND auth_credentials.provider = 'local'
        """
    )
