"""In-process synchronous event bus (driven adapter).

Dispatches domain events to registered handlers synchronously within
the same process.  Handler errors are logged but do **not** propagate —
a failing handler must never break the caller's transaction or flow.

Thread safety: this implementation is **not** thread-safe.  Each UoW
instance should own its own bus or the bus should be shared read-only
after handler registration is complete.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from shared_kernel.events import DomainEvent, EventHandler

logger = logging.getLogger(__name__)


class InProcessEventBus:
    """Synchronous in-process event bus.

    Usage::

        bus = InProcessEventBus()
        bus.subscribe(OrderPlaced, email_handler)
        bus.subscribe(OrderPlaced, analytics_handler)

        # Later, after UoW commit:
        bus.publish(collected_events)
    """

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[EventHandler]] = defaultdict(list)

    def subscribe(
        self,
        event_type: type[DomainEvent],
        handler: EventHandler,
    ) -> None:
        """Register a handler for a specific event type."""
        self._handlers[event_type].append(handler)

    def publish(self, events: list[DomainEvent]) -> None:
        """Dispatch each event to all handlers registered for its type.

        Handler exceptions are caught and logged — they never propagate.
        """
        for event in events:
            handlers = self._handlers.get(type(event), [])
            for handler in handlers:
                try:
                    handler.handle(event)
                except Exception:
                    logger.exception(
                        "Event handler %s failed for %s",
                        type(handler).__name__,
                        type(event).__name__,
                    )
