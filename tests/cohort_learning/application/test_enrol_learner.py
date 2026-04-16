"""Tests for EnrolLearner use case."""

import pytest

from cohort_learning.application.enrol_learner import EnrolLearnerUseCase
from cohort_learning.domain.cohort_role import CohortRole
from cohort_learning.domain.events import LearnerEnrolled
from shared_kernel.events import DomainEvent
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.cohort_learning.factories import make_cohort, make_active_cohort, save_cohort


class _SpyEventBus:
    """Spy event bus that records all published events."""

    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    def publish(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)


class TestEnrolLearnerUseCase:
    """EnrolLearner adds a learner to a forming cohort."""

    def test_enrols_learner(self) -> None:
        uow = FakeUnitOfWork()
        save_cohort(uow, make_cohort())
        use_case = EnrolLearnerUseCase(uow=uow)

        use_case.execute(
            cohort_id="c1",
            membership_id="mem1",
            learner_id="l1",
            caller_id="master1",
        )

        cohort = uow.cohorts.find_by_id("c1")
        assert cohort is not None
        assert cohort.active_learner_count == 1
        m = cohort.memberships[0]
        assert m.learner_id == "l1"
        assert m.role == CohortRole.LEARNER

    def test_commits_transaction(self) -> None:
        uow = FakeUnitOfWork()
        save_cohort(uow, make_cohort())
        use_case = EnrolLearnerUseCase(uow=uow)

        use_case.execute(
            cohort_id="c1",
            membership_id="mem1",
            learner_id="l1",
            caller_id="master1",
        )

        assert uow.committed is True

    def test_emits_learner_enrolled_event(self) -> None:
        spy_bus = _SpyEventBus()
        uow = FakeUnitOfWork(event_bus=spy_bus)
        save_cohort(uow, make_cohort())
        use_case = EnrolLearnerUseCase(uow=uow)

        use_case.execute(
            cohort_id="c1",
            membership_id="mem1",
            learner_id="l1",
            caller_id="master1",
        )

        enrolled_events = [
            e for e in spy_bus.published if isinstance(e, LearnerEnrolled)
        ]
        assert len(enrolled_events) == 1
        assert enrolled_events[0].learner_id == "l1"

    def test_raises_when_cohort_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = EnrolLearnerUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(
                cohort_id="nonexistent",
                membership_id="mem1",
                learner_id="l1",
                caller_id="master1",
            )

    def test_raises_when_caller_is_not_master(self) -> None:
        uow = FakeUnitOfWork()
        save_cohort(uow, make_cohort())
        use_case = EnrolLearnerUseCase(uow=uow)

        with pytest.raises(PermissionError, match="[Mm]aster"):
            use_case.execute(
                cohort_id="c1",
                membership_id="mem1",
                learner_id="l1",
                caller_id="intruder",
            )

    def test_raises_when_cohort_not_forming(self) -> None:
        uow = FakeUnitOfWork()
        save_cohort(uow, make_active_cohort())
        use_case = EnrolLearnerUseCase(uow=uow)

        with pytest.raises(ValueError, match="[Ff]orming"):
            use_case.execute(
                cohort_id="c1",
                membership_id="mem_new",
                learner_id="l_new",
                caller_id="master1",
            )
