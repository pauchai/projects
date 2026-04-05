"""Unit tests for InProcessEventBus — TDD Red-Green-Refactor."""

from dataclasses import dataclass

from shared_kernel.events import DomainEvent
from shared_kernel.in_process_event_bus import InProcessEventBus


# --- Test doubles ---


@dataclass(frozen=True)
class OrderPlaced(DomainEvent):
    order_id: str


@dataclass(frozen=True)
class OrderShipped(DomainEvent):
    order_id: str


class SpyHandler:
    """Spy: records all handled events for assertion."""

    def __init__(self) -> None:
        self.handled: list[DomainEvent] = []

    def handle(self, event: DomainEvent) -> None:
        self.handled.append(event)


class FailingHandler:
    """Handler that always raises — used to test error isolation."""

    def handle(self, event: DomainEvent) -> None:
        raise RuntimeError("handler failed")


# --- Tests ---


class TestInProcessEventBus:
    """Unit tests for the in-process synchronous event bus."""

    def test_publish_dispatches_to_registered_handler(self) -> None:
        bus = InProcessEventBus()
        handler = SpyHandler()
        bus.subscribe(OrderPlaced, handler)

        event = OrderPlaced(order_id="o1")
        bus.publish([event])

        assert handler.handled == [event]

    def test_publish_dispatches_to_multiple_handlers(self) -> None:
        bus = InProcessEventBus()
        handler_a = SpyHandler()
        handler_b = SpyHandler()
        bus.subscribe(OrderPlaced, handler_a)
        bus.subscribe(OrderPlaced, handler_b)

        event = OrderPlaced(order_id="o1")
        bus.publish([event])

        assert handler_a.handled == [event]
        assert handler_b.handled == [event]

    def test_publish_routes_events_to_correct_handlers(self) -> None:
        bus = InProcessEventBus()
        placed_handler = SpyHandler()
        shipped_handler = SpyHandler()
        bus.subscribe(OrderPlaced, placed_handler)
        bus.subscribe(OrderShipped, shipped_handler)

        placed = OrderPlaced(order_id="o1")
        shipped = OrderShipped(order_id="o2")
        bus.publish([placed, shipped])

        assert placed_handler.handled == [placed]
        assert shipped_handler.handled == [shipped]

    def test_publish_with_no_handlers_does_nothing(self) -> None:
        bus = InProcessEventBus()
        event = OrderPlaced(order_id="o1")

        # Should not raise
        bus.publish([event])

    def test_publish_empty_list_does_nothing(self) -> None:
        bus = InProcessEventBus()
        handler = SpyHandler()
        bus.subscribe(OrderPlaced, handler)

        bus.publish([])

        assert handler.handled == []

    def test_handler_error_does_not_stop_other_handlers(self) -> None:
        bus = InProcessEventBus()
        failing = FailingHandler()
        surviving = SpyHandler()
        bus.subscribe(OrderPlaced, failing)
        bus.subscribe(OrderPlaced, surviving)

        event = OrderPlaced(order_id="o1")
        bus.publish([event])

        # The surviving handler should still receive the event
        assert surviving.handled == [event]

    def test_handler_error_does_not_raise(self) -> None:
        bus = InProcessEventBus()
        bus.subscribe(OrderPlaced, FailingHandler())

        event = OrderPlaced(order_id="o1")
        # Should not raise despite handler failure
        bus.publish([event])

    def test_publish_multiple_events_sequentially(self) -> None:
        bus = InProcessEventBus()
        handler = SpyHandler()
        bus.subscribe(OrderPlaced, handler)

        events = [OrderPlaced(order_id="o1"), OrderPlaced(order_id="o2")]
        bus.publish(events)

        assert len(handler.handled) == 2
        assert handler.handled[0] == OrderPlaced(order_id="o1")
        assert handler.handled[1] == OrderPlaced(order_id="o2")
