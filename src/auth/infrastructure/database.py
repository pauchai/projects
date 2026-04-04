"""Database engine and session factory for the Auth bounded context.

Uses the same PostgreSQL instance as project_collaboration (shared infra),
but with its own MetaData and table namespace (auth_users, auth_credentials).
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DATABASE_URL = "postgresql://collab:collab@localhost:5434/project_collaboration"
TEST_DATABASE_URL = (
    "postgresql://collab_test:collab_test@localhost:5433/project_collaboration_test"
)


def get_engine(url: str | None = None) -> Engine:
    """Create a SQLAlchemy engine from a URL or DATABASE_URL env var."""
    database_url = url or os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    return create_engine(database_url, echo=False)


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a session factory bound to the given engine."""
    return sessionmaker(bind=engine, expire_on_commit=False)


def create_tables(engine: Engine) -> None:
    """Create all auth tables. For dev/test only (no Alembic yet)."""
    from auth.infrastructure.orm import metadata

    metadata.create_all(engine)


def drop_tables(engine: Engine) -> None:
    """Drop all auth tables. For dev/test only."""
    from auth.infrastructure.orm import metadata

    metadata.drop_all(engine)
