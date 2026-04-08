"""Integration test fixtures for the Auth bounded context.

Same SAVEPOINT isolation pattern as project_collaboration:
- Session-scoped engine creates/drops auth tables once.
- Per-test connection opens a transaction that is rolled back after the test.
- Per-test session uses SAVEPOINT so commit() inside UoW/repo doesn't escape.

Requires a running PostgreSQL test container (port 5433):
    docker compose up -d postgres-test
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import Connection, Engine, event
from sqlalchemy.orm import Session, sessionmaker

from auth.infrastructure.database import (
    TEST_DATABASE_URL,
    get_engine,
)
from shared_kernel.migration import downgrade_migrations, run_migrations


@pytest.fixture(scope="session")
def auth_engine() -> Generator[Engine, None, None]:
    """Create an engine for the test database, run migrations, yield, downgrade."""
    engine = get_engine(TEST_DATABASE_URL)
    downgrade_migrations(engine)
    run_migrations(engine)
    yield engine
    downgrade_migrations(engine)
    engine.dispose()


@pytest.fixture()
def auth_connection(auth_engine: Engine) -> Generator[Connection, None, None]:
    """Open a connection and begin a transaction; rollback after each test."""
    connection = auth_engine.connect()
    transaction = connection.begin()
    yield connection
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture()
def auth_session(auth_connection: Connection) -> Generator[Session, None, None]:
    """Create a Session bound to the test connection with SAVEPOINT isolation."""
    session = Session(bind=auth_connection)
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session: Session, transaction: object) -> None:
        if not session.in_nested_transaction():
            session.begin_nested()

    yield session
    session.close()


@pytest.fixture()
def auth_session_factory(auth_connection: Connection) -> sessionmaker[Session]:
    """Return a sessionmaker-like callable bound to the test connection.

    Used by SqlAlchemyUnitOfWork which expects a sessionmaker.
    """

    class _TestSessionFactory:
        def __call__(self) -> Session:
            session = Session(bind=auth_connection)
            session.begin_nested()

            @event.listens_for(session, "after_transaction_end")
            def restart_savepoint(session: Session, transaction: object) -> None:
                if not session.in_nested_transaction():
                    session.begin_nested()

            return session

    return _TestSessionFactory()  # type: ignore[return-value]
