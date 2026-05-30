"""SQLAlchemy ORM mapping for the Auth bounded context (Imperative Mapping).

Domain classes remain free of SQLAlchemy imports. Table definitions are kept
here alongside the mapping configuration. The mapper is triggered on module
import — any module that imports from ``orm`` will activate the mappings.

Key design decisions:
- Domain classes (User, Credential) have no SQLAlchemy dependencies.
- Credential is mapped as a child of User via relationship + cascade.
- ORM bypasses ``__init__`` on load (uses ``__new__`` + attribute population),
  so validation in ``__init__`` does not re-run for data from the DB.
- TelegramAuthRequest is NOT mapped here — it is stored in Redis with
  automatic TTL expiration (see ``redis_telegram_auth_request_repository``).
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
from sqlalchemy.orm import registry, relationship

from auth.domain.user import Credential, User

# ---------------------------------------------------------------------------
# Registry (manages MetaData + class ↔ table mappings)
# ---------------------------------------------------------------------------

mapper_registry = registry()
metadata: MetaData = mapper_registry.metadata

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
    Column("status", String(20), nullable=False, server_default="active"),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column(
        "inviter_id",
        String(255),
        ForeignKey("auth_users.user_id", ondelete="SET NULL"),
        nullable=True,
    ),
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

# ---------------------------------------------------------------------------
# Imperative mappings
# ---------------------------------------------------------------------------

mapper_registry.map_imperatively(Credential, credentials_table)

mapper_registry.map_imperatively(
    User,
    users_table,
    properties={
        "credentials": relationship(
            Credential,
            cascade="all, delete-orphan",
            passive_deletes=True,
        ),
    },
)

