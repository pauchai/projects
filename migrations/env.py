"""Alembic environment configuration.

Combines MetaData from all bounded contexts (auth, project_collaboration,
cohort_learning) into a single target for autogenerate support. All contexts
share the same PostgreSQL database but maintain separate ORM registries.

Database URL resolution (in priority order):
1. DATABASE_URL environment variable
2. sqlalchemy.url from alembic.ini
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy import engine_from_config, pool

from alembic import context

# Load .env so DATABASE_URL is available
load_dotenv()

# ---------------------------------------------------------------------------
# Alembic Config object
# ---------------------------------------------------------------------------

config = context.config

# Override sqlalchemy.url with DATABASE_URL env var if present.
# Skip if the URL was already set programmatically (e.g., by run_migrations()).
if not config.get_main_option("is_programmatic"):
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Target MetaData — combine both bounded contexts
# ---------------------------------------------------------------------------

# Importing the ORM modules triggers imperative mappings and populates
# the MetaData objects with table definitions.
from auth.infrastructure.orm import metadata as auth_metadata
from cohort_learning.infrastructure.orm import metadata as cohort_metadata
from project_collaboration.infrastructure.orm import metadata as collab_metadata

# Merge all MetaData into a single target for autogenerate.
from sqlalchemy import MetaData

target_metadata = MetaData()

for table in auth_metadata.tables.values():
    table.to_metadata(target_metadata)

for table in collab_metadata.tables.values():
    table.to_metadata(target_metadata)

for table in cohort_metadata.tables.values():
    table.to_metadata(target_metadata)

# Tables that exist in the DB but are NOT managed by Alembic.
# Autogenerate will ignore them instead of emitting DROP statements.
EXCLUDED_TABLES: set[str] = {"telegram_auth_requests"}


def include_object(
    object: sa.schema.SchemaItem,  # noqa: A002
    name: str | None,
    type_: str,
    reflected: bool,
    compare_to: sa.schema.SchemaItem | None,
) -> bool:
    """Filter out excluded tables from autogenerate comparison."""
    if type_ == "table" and name in EXCLUDED_TABLES:
        return False
    return True


# ---------------------------------------------------------------------------
# Migration runners
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL and emits SQL to stdout
    instead of executing against the database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an Engine and runs migrations against a live database.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
