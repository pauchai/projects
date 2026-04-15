"""Tests for FormCohort use case."""

import pytest

from cohort_learning.application.form_cohort import FormCohortUseCase
from cohort_learning.domain.cohort_status import CohortStatus
from cohort_learning.domain.events import CohortFormed
from shared_kernel.events import DomainEvent
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork


class _SpyEventBus:
    """Spy event bus that records all published events."""

    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    def publish(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)


class TestFormCohortUseCase:
    """FormCohort creates a cohort in Forming status."""

    def test_creates_cohort_in_forming_status(self) -> None:
        uow = FakeUnitOfWork()
        use_case = FormCohortUseCase(uow=uow)

        cohort = use_case.execute(
            cohort_id="c1",
            master_id="m1",
            module_id="mod1",
        )

        assert cohort.status == CohortStatus.FORMING
        assert cohort.cohort_id == "c1"
        assert cohort.master_id == "m1"
        assert cohort.module_id == "mod1"

    def test_saves_cohort_to_repository(self) -> None:
        uow = FakeUnitOfWork()
        use_case = FormCohortUseCase(uow=uow)

        use_case.execute(cohort_id="c1", master_id="m1", module_id="mod1")

        assert uow.cohorts.find_by_id("c1") is not None

    def test_commits_transaction(self) -> None:
        uow = FakeUnitOfWork()
        use_case = FormCohortUseCase(uow=uow)

        use_case.execute(cohort_id="c1", master_id="m1", module_id="mod1")

        assert uow.committed is True

    def test_emits_cohort_formed_event(self) -> None:
        spy_bus = _SpyEventBus()
        uow = FakeUnitOfWork(event_bus=spy_bus)
        use_case = FormCohortUseCase(uow=uow)

        use_case.execute(cohort_id="c1", master_id="m1", module_id="mod1")

        assert len(spy_bus.published) == 1
        assert isinstance(spy_bus.published[0], CohortFormed)
        assert spy_bus.published[0].cohort_id == "c1"

    def test_starts_with_no_memberships(self) -> None:
        uow = FakeUnitOfWork()
        use_case = FormCohortUseCase(uow=uow)

        cohort = use_case.execute(cohort_id="c1", master_id="m1", module_id="mod1")

        assert cohort.memberships == []
