"""Tests for cohort_learning domain ports — CohortRepository and UnitOfWork."""

import pytest

from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.domain.events import CohortFormed
from tests.cohort_learning.factories import make_cohort
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork


class TestFakeCohortRepository:
    """Verify the fake repository satisfies the CohortRepository protocol."""

    def test_save_and_find_by_id(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_cohort(cohort_id="c1")
        with uow:
            uow.cohorts.save(cohort)
            uow.commit()
        found = uow.cohorts.find_by_id("c1")
        assert found is not None
        assert found.cohort_id == "c1"

    def test_find_by_id_returns_none_for_missing(self) -> None:
        uow = FakeUnitOfWork()
        assert uow.cohorts.find_by_id("nonexistent") is None

    def test_save_collects_events(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_cohort(cohort_id="c1")
        with uow:
            uow.cohorts.save(cohort)
            # Events should have been collected from the aggregate
            assert len(uow._pending_events) >= 1
            uow.commit()


class TestFakeUnitOfWork:
    """Verify commit/rollback semantics of the fake UoW."""

    def test_commit_keeps_changes(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_cohort(cohort_id="c1")
        with uow:
            uow.cohorts.save(cohort)
            uow.commit()
        assert uow.cohorts.find_by_id("c1") is not None

    def test_rollback_discards_changes(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_cohort(cohort_id="c1")
        with uow:
            uow.cohorts.save(cohort)
            uow.rollback()
        assert uow.cohorts.find_by_id("c1") is None

    def test_exit_without_commit_rolls_back(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_cohort(cohort_id="c1")
        with uow:
            uow.cohorts.save(cohort)
            # no commit — should rollback on exit
        assert uow.cohorts.find_by_id("c1") is None

    def test_committed_flag(self) -> None:
        uow = FakeUnitOfWork()
        assert uow.committed is False
        with uow:
            uow.cohorts.save(make_cohort())
            uow.commit()
        assert uow.committed is True
