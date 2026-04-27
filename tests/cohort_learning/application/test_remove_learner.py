"""Tests for RemoveLearner use case."""

import pytest

from cohort_learning.application.remove_learner import RemoveLearnerUseCase
from cohort_learning.domain.events import LearnerRemoved
from shared_kernel.events import DomainEvent
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.cohort_learning.factories import make_cohort, save_cohort


class _SpyEventBus:
    """Spy event bus that records all published events."""

    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    def publish(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)


class TestRemoveLearnerUseCase:
    """RemoveLearner deactivates a learner's membership."""

    def test_removes_learner(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_cohort()
        cohort.enrol_learner(membership_id="mem1", learner_id="l1")
        cohort.collect_events()
        save_cohort(uow, cohort)
        use_case = RemoveLearnerUseCase(uow=uow)

        use_case.execute(
            cohort_id="c1",
            membership_id="mem1",
            caller_id="master1",
        )

        cohort = uow.cohorts.find_by_id("c1")
        assert cohort is not None
        assert cohort.active_learner_count == 0
        assert cohort.memberships[0].is_active is False

    def test_commits_transaction(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_cohort()
        cohort.enrol_learner(membership_id="mem1", learner_id="l1")
        cohort.collect_events()
        save_cohort(uow, cohort)
        use_case = RemoveLearnerUseCase(uow=uow)

        use_case.execute(cohort_id="c1", membership_id="mem1", caller_id="master1")

        assert uow.committed is True

    def test_emits_learner_removed_event(self) -> None:
        spy_bus = _SpyEventBus()
        uow = FakeUnitOfWork(event_bus=spy_bus)
        cohort = make_cohort()
        cohort.enrol_learner(membership_id="mem1", learner_id="l1")
        cohort.collect_events()
        save_cohort(uow, cohort)
        use_case = RemoveLearnerUseCase(uow=uow)

        use_case.execute(cohort_id="c1", membership_id="mem1", caller_id="master1")

        removed_events = [e for e in spy_bus.published if isinstance(e, LearnerRemoved)]
        assert len(removed_events) == 1
        assert removed_events[0].learner_id == "l1"

    def test_raises_when_cohort_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = RemoveLearnerUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(
                cohort_id="nonexistent",
                membership_id="mem1",
                caller_id="master1",
            )

    def test_raises_when_caller_is_not_master(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_cohort()
        cohort.enrol_learner(membership_id="mem1", learner_id="l1")
        cohort.collect_events()
        save_cohort(uow, cohort)
        use_case = RemoveLearnerUseCase(uow=uow)

        with pytest.raises(PermissionError, match="[Mm]aster"):
            use_case.execute(
                cohort_id="c1",
                membership_id="mem1",
                caller_id="intruder",
            )

    def test_raises_when_membership_not_found(self) -> None:
        uow = FakeUnitOfWork()
        save_cohort(uow, make_cohort())
        use_case = RemoveLearnerUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(
                cohort_id="c1",
                membership_id="nonexistent",
                caller_id="master1",
            )
