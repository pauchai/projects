"""FastAPI dependency injection: provides UnitOfWork instances to route handlers."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from project_collaboration.infrastructure.database import (
    DEFAULT_DATABASE_URL,
    get_engine,
    get_session_factory,
)
from project_collaboration.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)

# Module-level singletons, initialized lazily.
_session_factory: sessionmaker[Session] | None = None


def _get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        engine = get_engine(DEFAULT_DATABASE_URL)
        _session_factory = get_session_factory(engine)
    return _session_factory


def get_uow() -> Generator[SqlAlchemyUnitOfWork, None, None]:
    """FastAPI dependency that yields a SqlAlchemyUnitOfWork.

    Use cases manage the UoW lifecycle themselves (``with uow:``),
    so we just need to construct it with the session factory.
    """
    uow = SqlAlchemyUnitOfWork(_get_session_factory())
    yield uow


def override_session_factory(factory: sessionmaker[Session]) -> None:
    """Override the module-level session factory (used in tests)."""
    global _session_factory
    _session_factory = factory
