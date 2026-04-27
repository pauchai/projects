"""Tests for application-layer shared helpers."""

import pytest

from cohort_learning.application._helpers import (
    get_cohort_or_raise,
    require_cohort_member,
    require_master,
    require_master_or_curator,
)
from cohort_learning.domain.cohort_role import CohortRole
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.cohort_learning.factories import make_cohort, make_active_cohort, save_cohort


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


class TestRequireMasterOrCurator:
    """require_master_or_curator allows master or module curator to proceed."""

    def test_passes_for_master(self) -> None:
        cohort = make_cohort(master_id="m1")
        require_master_or_curator(cohort, "m1")  # should not raise

    def test_passes_for_module_curator(self) -> None:
        cohort = make_active_cohort()
        # Promote learner1 to MODULE_CURATOR
        membership = cohort.find_membership_by_learner_id("learner1")
        assert membership is not None
        membership.promote_to(CohortRole.TOPIC_EXPERT)
        membership.promote_to(CohortRole.MODULE_CURATOR)
        require_master_or_curator(cohort, "learner1")  # should not raise

    def test_raises_for_plain_learner(self) -> None:
        cohort = make_active_cohort()
        with pytest.raises(PermissionError, match="master or module curator"):
            require_master_or_curator(cohort, "learner1")

    def test_raises_for_topic_expert(self) -> None:
        cohort = make_active_cohort()
        membership = cohort.find_membership_by_learner_id("learner1")
        assert membership is not None
        membership.promote_to(CohortRole.TOPIC_EXPERT)
        with pytest.raises(PermissionError, match="master or module curator"):
            require_master_or_curator(cohort, "learner1")

    def test_raises_for_non_member(self) -> None:
        cohort = make_active_cohort()
        with pytest.raises(PermissionError, match="master or module curator"):
            require_master_or_curator(cohort, "outsider")


class TestRequireCohortMember:
    """require_cohort_member allows active cohort members to proceed."""

    def test_passes_for_active_member(self) -> None:
        cohort = make_active_cohort()
        require_cohort_member(cohort, "learner1")  # should not raise

    def test_raises_for_non_member(self) -> None:
        cohort = make_active_cohort()
        with pytest.raises(PermissionError, match="not an active member"):
            require_cohort_member(cohort, "outsider")
