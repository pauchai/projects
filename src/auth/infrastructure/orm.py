"""SQLAlchemy table definitions for the Auth bounded context (Core only).

Mirrors the approach in project_collaboration: pure Core tables, no ORM mapping.
Domain classes stay free of SQLAlchemy imports. Repositories handle persistence
and reconstitution using Core queries + object.__new__.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    MetaData,
    String,
    Table,
    UniqueConstraint,
)

metadata = MetaData()

# ---------------------------------------------------------------------------
# Table definitions
# ---------------------------------------------------------------------------

users_table = Table(
    "auth_users",
    metadata,
    Column("user_id", String(255), primary_key=True),
    Column("email", String(320), nullable=False, unique=True),
    Column("display_name", String(100), nullable=False),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

credentials_table = Table(
    "auth_credentials",
    metadata,
    Column("credential_id", String(255), primary_key=True),
    Column(
        "user_id",
        String(255),
        ForeignKey("auth_users.user_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("provider", String(50), nullable=False),
    Column("provider_user_id", String(320), nullable=False),
    Column("hashed_secret", String(512), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("user_id", "provider", name="uq_user_provider"),
)
