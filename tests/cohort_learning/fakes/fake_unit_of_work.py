"""Fake in-memory implementation of UnitOfWork for testing."""

import copy

from cohort_learning.domain.learning_cohort import LearningCohort
from shared_kernel.events import DomainEvent, EventBus


class _FakeCohortRepository:
    """In-memory CohortRepository used within FakeUnitOfWork."""

    def __init__(self, uow: "FakeUnitOfWork") -> None:
        self._storage: dict[str, LearningCohort] = {}
        self._uow = uow

    def find_by_id(self, cohort_id: str) -> LearningCohort | None:
        return self._storage.get(cohort_id)

    def save(self, cohort: LearningCohort) -> None:
        events = cohort.collect_events()
        self._uow.collect_events(events)
        self._storage[cohort.cohort_id] = cohort

    def snapshot(self) -> dict[str, LearningCohort]:
        """Return a deep copy of the storage for rollback support."""
        return copy.deepcopy(self._storage)

    def restore(self, snapshot: dict[str, LearningCohort]) -> None:
        """Restore storage from a snapshot."""
        self._storage = snapshot


class FakeUnitOfWork:
    """Fake UoW for testing: in-memory with commit/rollback semantics.

    On __enter__, snapshots current state. On commit(), keeps changes.
    On rollback() or __exit__ without commit, restores the snapshot.
    Supports optional event bus for verifying event publication.
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self.cohorts = _FakeCohortRepository(self)
        self.committed = False
        self._cohorts_snapshot: dict[str, LearningCohort] | None = None
        self._event_bus = event_bus
        self._pending_events: list[DomainEvent] = []

    def __enter__(self) -> "FakeUnitOfWork":
        self.committed = False
        self._cohorts_snapshot = self.cohorts.snapshot()
        return self

    def __exit__(self, *args: object) -> None:
        if not self.committed:
            self.rollback()
        self._cohorts_snapshot = None

    def commit(self) -> None:
        self.committed = True
        if self._event_bus and self._pending_events:
            self._event_bus.publish(self._pending_events)
        self._pending_events.clear()
        self._cohorts_snapshot = None

    def rollback(self) -> None:
        if self._cohorts_snapshot is not None:
            self.cohorts.restore(self._cohorts_snapshot)
            self._cohorts_snapshot = None
        self._pending_events.clear()

    def collect_events(self, events: list[DomainEvent]) -> None:
        """Accumulate domain events for publishing after commit."""
        self._pending_events.extend(events)
