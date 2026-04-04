"""Integration test fixtures: PostgreSQL engine, session, table lifecycle.

Each test runs inside a top-level transaction that is rolled back after the test.
Sessions use a nested (SAVEPOINT) transaction so that ``session.commit()``
commits only the savepoint, not the real transaction.  The outer connection
fixture rolls back everything after the test — giving full isolation.

Requires a running PostgreSQL test container (port 5433):
    docker compose up -d postgres-test
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import Connection, Engine, event
from sqlalchemy.orm import Session, sessionmaker

from project_collaboration.infrastructure.database import (
    TEST_DATABASE_URL,
    create_tables,
    drop_tables,
    get_engine,
)


@pytest.fixture(scope="session")
def integration_engine() -> Generator[Engine, None, None]:
    """Create an engine for the test database, create tables, yield, drop tables."""
    engine = get_engine(TEST_DATABASE_URL)
    drop_tables(engine)
    create_tables(engine)
    yield engine
    drop_tables(engine)
    engine.dispose()


@pytest.fixture()
def integration_connection(
    integration_engine: Engine,
) -> Generator[Connection, None, None]:
    """Open a connection and begin a transaction; rollback after each test."""
    connection = integration_engine.connect()
    transaction = connection.begin()
    yield connection
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture()
def integration_session(
    integration_connection: Connection,
) -> Generator[Session, None, None]:
    """Create a Session bound to the test connection/transaction.

    The session uses a nested transaction (SAVEPOINT).  When the session
    calls ``commit()``, it commits only the savepoint.  After each commit
    we immediately start a new nested transaction so subsequent operations
    stay within the outer transaction that will be rolled back by the
    ``integration_connection`` fixture.
    """
    session = Session(bind=integration_connection)
    # Start a nested (SAVEPOINT) transaction
    session.begin_nested()

    # After each commit, re-start a nested transaction so the outer
    # connection-level transaction is never committed.
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session: Session, transaction: object) -> None:
        if not session.in_nested_transaction():
            session.begin_nested()

    yield session
    session.close()


@pytest.fixture()
def integration_session_factory(
    integration_connection: Connection,
) -> sessionmaker[Session]:
    """Return a sessionmaker-like callable that produces sessions bound to the test connection.

    Used by ``SqlAlchemyUnitOfWork`` which expects a sessionmaker.
    The UoW calls ``session_factory()`` to get a new session; we need that
    session bound to the same connection (so rollback works).
    """

    class _TestSessionFactory:
        """Callable that mimics sessionmaker but binds to the test connection."""

        def __call__(self) -> Session:
            session = Session(bind=integration_connection)
            session.begin_nested()

            @event.listens_for(session, "after_transaction_end")
            def restart_savepoint(session: Session, transaction: object) -> None:
                if not session.in_nested_transaction():
                    session.begin_nested()

            return session

    return _TestSessionFactory()  # type: ignore[return-value]
