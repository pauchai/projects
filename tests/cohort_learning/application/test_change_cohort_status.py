"""Tests for ChangeCohortStatus use cases (activate, begin_completing, graduate, cancel)."""

import pytest

from cohort_learning.application.change_cohort_status import (
    ActivateCohortUseCase,
    BeginCompletingCohortUseCase,
    GraduateCohortUseCase,
    CancelCohortUseCase,
)
from cohort_learning.domain.cohort_status import CohortStatus
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.cohort_learning.factories import make_cohort, make_active_cohort, save_cohort


# =============================================================================
# ActivateCohortUseCase
# =============================================================================


class TestActivateCohortUseCase:
    def test_activates_forming_cohort(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_cohort()
        for i in range(5):
            cohort.enrol_learner(membership_id=f"mem{i}", learner_id=f"l{i}")
        cohort.collect_events()
        save_cohort(uow, cohort)
        use_case = ActivateCohortUseCase(uow=uow)

        use_case.execute(cohort_id="c1", caller_id="master1")

        cohort = uow.cohorts.find_by_id("c1")
        assert cohort is not None
        assert cohort.status == CohortStatus.ACTIVE

    def test_raises_when_cohort_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = ActivateCohortUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(cohort_id="c999", caller_id="master1")

    def test_raises_when_caller_is_not_master(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_cohort()
        for i in range(5):
            cohort.enrol_learner(membership_id=f"mem{i}", learner_id=f"l{i}")
        cohort.collect_events()
        save_cohort(uow, cohort)
        use_case = ActivateCohortUseCase(uow=uow)

        with pytest.raises(PermissionError, match="[Mm]aster"):
            use_case.execute(cohort_id="c1", caller_id="intruder")

    def test_raises_when_not_enough_learners(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_cohort()
        cohort.enrol_learner(membership_id="mem1", learner_id="l1")
        cohort.collect_events()
        save_cohort(uow, cohort)
        use_case = ActivateCohortUseCase(uow=uow)

        with pytest.raises(ValueError, match="minimum"):
            use_case.execute(cohort_id="c1", caller_id="master1")

    def test_raises_when_already_active(self) -> None:
        uow = FakeUnitOfWork()
        save_cohort(uow, make_active_cohort())
        use_case = ActivateCohortUseCase(uow=uow)

        with pytest.raises(ValueError, match="[Cc]annot transition"):
            use_case.execute(cohort_id="c1", caller_id="master1")


# =============================================================================
# BeginCompletingCohortUseCase
# =============================================================================


class TestBeginCompletingCohortUseCase:
    def test_transitions_active_to_completing(self) -> None:
        uow = FakeUnitOfWork()
        save_cohort(uow, make_active_cohort())
        use_case = BeginCompletingCohortUseCase(uow=uow)

        use_case.execute(cohort_id="c1", caller_id="master1")

        cohort = uow.cohorts.find_by_id("c1")
        assert cohort is not None
        assert cohort.status == CohortStatus.COMPLETING

    def test_raises_when_cohort_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = BeginCompletingCohortUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(cohort_id="c999", caller_id="master1")

    def test_raises_when_caller_is_not_master(self) -> None:
        uow = FakeUnitOfWork()
        save_cohort(uow, make_active_cohort())
        use_case = BeginCompletingCohortUseCase(uow=uow)

        with pytest.raises(PermissionError, match="[Mm]aster"):
            use_case.execute(cohort_id="c1", caller_id="intruder")

    def test_raises_when_not_active(self) -> None:
        uow = FakeUnitOfWork()
        save_cohort(uow, make_cohort())
        use_case = BeginCompletingCohortUseCase(uow=uow)

        with pytest.raises(ValueError, match="[Cc]annot transition"):
            use_case.execute(cohort_id="c1", caller_id="master1")


# =============================================================================
# GraduateCohortUseCase
# =============================================================================


class TestGraduateCohortUseCase:
    def test_graduates_completing_cohort(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        cohort.begin_completing()
        cohort.collect_events()
        save_cohort(uow, cohort)
        use_case = GraduateCohortUseCase(uow=uow)

        use_case.execute(cohort_id="c1", caller_id="master1")

        cohort = uow.cohorts.find_by_id("c1")
        assert cohort is not None
        assert cohort.status == CohortStatus.GRADUATED

    def test_raises_when_cohort_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = GraduateCohortUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(cohort_id="c999", caller_id="master1")

    def test_raises_when_caller_is_not_master(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        cohort.begin_completing()
        cohort.collect_events()
        save_cohort(uow, cohort)
        use_case = GraduateCohortUseCase(uow=uow)

        with pytest.raises(PermissionError, match="[Mm]aster"):
            use_case.execute(cohort_id="c1", caller_id="intruder")

    def test_raises_when_not_completing(self) -> None:
        uow = FakeUnitOfWork()
        save_cohort(uow, make_active_cohort())
        use_case = GraduateCohortUseCase(uow=uow)

        with pytest.raises(ValueError, match="[Cc]annot transition"):
            use_case.execute(cohort_id="c1", caller_id="master1")


# =============================================================================
# CancelCohortUseCase
# =============================================================================


class TestCancelCohortUseCase:
    def test_cancels_forming_cohort(self) -> None:
        uow = FakeUnitOfWork()
        save_cohort(uow, make_cohort())
        use_case = CancelCohortUseCase(uow=uow)

        use_case.execute(cohort_id="c1", caller_id="master1")

        cohort = uow.cohorts.find_by_id("c1")
        assert cohort is not None
        assert cohort.status == CohortStatus.CANCELLED

    def test_cancels_active_cohort(self) -> None:
        uow = FakeUnitOfWork()
        save_cohort(uow, make_active_cohort())
        use_case = CancelCohortUseCase(uow=uow)

        use_case.execute(cohort_id="c1", caller_id="master1")

        cohort = uow.cohorts.find_by_id("c1")
        assert cohort is not None
        assert cohort.status == CohortStatus.CANCELLED

    def test_raises_when_cohort_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CancelCohortUseCase(uow=uow)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(cohort_id="c999", caller_id="master1")

    def test_raises_when_caller_is_not_master(self) -> None:
        uow = FakeUnitOfWork()
        save_cohort(uow, make_cohort())
        use_case = CancelCohortUseCase(uow=uow)

        with pytest.raises(PermissionError, match="[Mm]aster"):
            use_case.execute(cohort_id="c1", caller_id="intruder")

    def test_raises_when_already_graduated(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_active_cohort()
        cohort.begin_completing()
        cohort.graduate()
        cohort.collect_events()
        save_cohort(uow, cohort)
        use_case = CancelCohortUseCase(uow=uow)

        with pytest.raises(ValueError, match="[Cc]annot transition"):
            use_case.execute(cohort_id="c1", caller_id="master1")
