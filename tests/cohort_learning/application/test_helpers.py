"""Tests for application-layer shared helpers."""

import pytest

from cohort_learning.application._helpers import get_cohort_or_raise, require_master
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.cohort_learning.factories import make_cohort, save_cohort


class TestGetCohortOrRaise:
    def test_returns_cohort_when_found(self) -> None:
        uow = FakeUnitOfWork()
        save_cohort(uow, make_cohort(cohort_id="c1"))
        with uow:
            cohort = get_cohort_or_raise(uow, "c1")
        assert cohort.cohort_id == "c1"

    def test_raises_when_not_found(self) -> None:
        uow = FakeUnitOfWork()
        with uow:
            with pytest.raises(LookupError, match="not found"):
                get_cohort_or_raise(uow, "nonexistent")


class TestRequireMaster:
    def test_passes_for_master(self) -> None:
        cohort = make_cohort(master_id="m1")
        require_master(cohort, "m1")  # should not raise

    def test_raises_for_non_master(self) -> None:
        cohort = make_cohort(master_id="m1")
        with pytest.raises(PermissionError, match="[Mm]aster"):
            require_master(cohort, "intruder")
