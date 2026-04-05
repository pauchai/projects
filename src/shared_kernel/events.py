"""Base domain event types and event bus protocol for all bounded contexts.

Provides:
- ``DomainEvent`` — immutable base class for all domain events.
- ``EventHandler`` — protocol for event handlers (driven port).
- ``EventBus`` — protocol for event publishing (driven port).

Domain classes inherit from ``DomainEvent``.  Infrastructure provides
``EventBus`` implementations (e.g., ``InProcessEventBus``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events across bounded contexts."""


class EventHandler(Protocol):
    """Port: handles a single domain event.

    Implementations should be idempotent — the same event may be
    delivered more than once in edge cases.
    """

    def handle(self, event: DomainEvent) -> None: ...


class EventBus(Protocol):
    """Port: publishes domain events to registered handlers.

    Called by UnitOfWork after a successful ``commit()``.  Handlers
    execute synchronously in the same process.
    """

    def publish(self, events: list[DomainEvent]) -> None: ...
