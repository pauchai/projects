"""FastAPI dependency injection for the Cohort Learning bounded context.

Provides:
- ``get_cohort_uow``: yields a SqlAlchemyUnitOfWork for cohort learning.
- ``get_current_user_id``: re-exported from project_collaboration for convenience.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from project_collaboration.api.dependencies import get_current_user_id  # noqa: F401
from project_collaboration.infrastructure.database import (
    get_engine,
    get_session_factory,
)
from cohort_learning.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from shared_kernel.events import EventBus

# Module-level singletons, initialized lazily.
_session_factory: sessionmaker[Session] | None = None
_event_bus: EventBus | None = None


def _get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = get_session_factory(engine)
    return _session_factory


def get_cohort_uow() -> Generator[SqlAlchemyUnitOfWork, None, None]:
    """FastAPI dependency that yields a SqlAlchemyUnitOfWork for cohort learning.

    Use cases manage the UoW lifecycle themselves (``with uow:``),
    so we just need to construct it with the session factory and event bus.
    """
    uow = SqlAlchemyUnitOfWork(_get_session_factory(), event_bus=_event_bus)
    yield uow


def override_session_factory(factory: sessionmaker[Session]) -> None:
    """Override the module-level session factory (used in tests)."""
    global _session_factory
    _session_factory = factory


def set_event_bus(bus: EventBus | None) -> None:
    """Set the module-level event bus.

    Called once at application startup to wire up domain event handlers.
    Pass ``None`` to disable event publishing.
    """
    global _event_bus
    _event_bus = bus
