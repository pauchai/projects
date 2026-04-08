"""SQLAlchemy ORM mapping for the Auth bounded context (Imperative Mapping).

Domain classes remain free of SQLAlchemy imports. Table definitions are kept
here alongside the mapping configuration. The mapper is triggered on module
import — any module that imports from ``orm`` will activate the mappings.

Key design decisions:
- Domain classes (User, Credential) have no SQLAlchemy dependencies.
- Credential is mapped as a child of User via relationship + cascade.
- ORM bypasses ``__init__`` on load (uses ``__new__`` + attribute population),
  so validation in ``__init__`` does not re-run for data from the DB.
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

from auth.domain.telegram_auth_request import TelegramAuthRequest
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

telegram_auth_requests_table = Table(
    "telegram_auth_requests",
    metadata,
    Column("auth_code", String(255), primary_key=True),
    Column("state", String(255), nullable=False),
    Column("authorization_code", String(255), nullable=True, unique=True),
    Column("telegram_user_id", String(255), nullable=True),
    Column("telegram_username", String(255), nullable=True),
    Column("telegram_first_name", String(255), nullable=True),
    Column("is_used", Boolean, nullable=False, default=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

# ---------------------------------------------------------------------------
# Imperative mappings
# ---------------------------------------------------------------------------

mapper_registry.map_imperatively(Credential, credentials_table)

mapper_registry.map_imperatively(TelegramAuthRequest, telegram_auth_requests_table)

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
