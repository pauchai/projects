"""SQLAlchemy implementation of UnitOfWork for the Auth bounded context.

Supports optional event publishing: when an ``EventBus`` is provided,
domain events collected during ``save()`` are published **after** a
successful ``commit()``.  If no bus is given, events are silently
discarded.

Note: The Auth context does not currently emit domain events, but this
infrastructure is in place for future use (e.g., UserRegistered,
UserDeactivated).
"""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from shared_kernel.events import DomainEvent, EventBus
from auth.infrastructure.sqlalchemy_repository import SqlAlchemyUserRepository


class SqlAlchemyUnitOfWork:
    """UnitOfWork backed by a SQLAlchemy Session.

    Implements the UnitOfWork Protocol defined in ``auth.domain.ports``.
    Application Services manage the lifecycle: ``with uow: ... uow.commit()``.
    """

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        event_bus: EventBus | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._event_bus = event_bus
        self._pending_events: list[DomainEvent] = []

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._session_factory()
        self.users = SqlAlchemyUserRepository(self._session)
        return self

    def __exit__(self, exc_type: type[BaseException] | None, *args: object) -> None:
        if exc_type is not None:
            self._session.rollback()
            self._pending_events.clear()
        self._session.close()

    def commit(self) -> None:
        """Persist changes and publish collected domain events."""
        self._session.commit()
        if self._event_bus and self._pending_events:
            self._event_bus.publish(self._pending_events)
        self._pending_events.clear()

    def rollback(self) -> None:
        self._session.rollback()
        self._pending_events.clear()

    def collect_events(self, events: list[DomainEvent]) -> None:
        """Accumulate domain events for publishing after commit.

        Called by the repository when an aggregate is saved.
        """
        self._pending_events.extend(events)
