"""FastAPI dependency injection for the Guarantorship bounded context."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from project_collaboration.infrastructure.database import (
    get_engine,
    get_session_factory,
)
from guarantorship.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyGuarantorshipUnitOfWork,
)

_session_factory: sessionmaker[Session] | None = None


def _get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = get_session_factory(engine)
    return _session_factory


def get_guarantorship_uow() -> Generator[SqlAlchemyGuarantorshipUnitOfWork, None, None]:
    """FastAPI dependency that yields a SqlAlchemyGuarantorshipUnitOfWork."""
    uow = SqlAlchemyGuarantorshipUnitOfWork(_get_session_factory())
    yield uow
