"""Fake in-memory UnitOfWork for Partnership bounded context tests."""

from __future__ import annotations

import copy

from partnership.domain.commission import Commission
from shared_kernel.events import DomainEvent, EventBus


class _FakeCommissionRepository:
    """In-memory CommissionRepository used within FakeUnitOfWork."""

    def __init__(self, uow: "FakeUnitOfWork") -> None:
        self._storage: dict[str, Commission] = {}
        self._uow = uow

    def find_by_id(self, commission_id: str) -> Commission | None:
        return self._storage.get(commission_id)

    def save(self, commission: Commission) -> None:
        events = commission.collect_events()
        self._uow.collect_events(events)
        self._storage[commission.commission_id] = commission

    def find_by_curator(self, curator_id: str) -> list[Commission]:
        return [c for c in self._storage.values() if c.curator_id == curator_id]

    def find_by_cohort(self, cohort_id: str) -> list[Commission]:
        return [c for c in self._storage.values() if c.cohort_id == cohort_id]

    def snapshot(self) -> dict[str, Commission]:
        return copy.deepcopy(self._storage)

    def restore(self, snapshot: dict[str, Commission]) -> None:
        self._storage = snapshot


class FakeUnitOfWork:
    """Fake UoW for Partnership testing: in-memory with commit/rollback semantics."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self.commissions = _FakeCommissionRepository(self)
        self.committed = False
        self._snapshots: dict[str, object] | None = None
        self._event_bus = event_bus
        self._pending_events: list[DomainEvent] = []

    def __enter__(self) -> "FakeUnitOfWork":
        self.committed = False
        self._snapshots = {"commissions": self.commissions.snapshot()}
        return self

    def __exit__(self, *args: object) -> None:
        if not self.committed:
            self.rollback()
        self._snapshots = None

    def commit(self) -> None:
        self.committed = True
        if self._event_bus and self._pending_events:
            self._event_bus.publish(self._pending_events)
        self._pending_events.clear()
        self._snapshots = None

    def rollback(self) -> None:
        if self._snapshots is not None:
            self.commissions.restore(self._snapshots["commissions"])  # type: ignore[arg-type]
            self._snapshots = None
        self._pending_events.clear()

    def collect_events(self, events: list[DomainEvent]) -> None:
        """Accumulate domain events for publishing after commit."""
        self._pending_events.extend(events)
