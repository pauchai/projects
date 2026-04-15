"""Tests for LearningCohort aggregate root."""

import pytest
from datetime import datetime, timezone

from cohort_learning.domain.cohort_status import CohortStatus
from cohort_learning.domain.cohort_role import CohortRole
from cohort_learning.domain.events import (
    CohortFormed,
    CohortActivated,
    CohortGraduated,
    CohortCancelled,
    LearnerEnrolled,
    LearnerRemoved,
)
from tests.cohort_learning.factories import make_cohort, make_active_cohort


# =============================================================================
# Cohort creation
# =============================================================================


class TestCohortCreation:
    def test_creates_cohort_in_forming_status(self) -> None:
        cohort = make_cohort()
        assert cohort.status == CohortStatus.FORMING

    def test_stores_basic_attributes(self) -> None:
        cohort = make_cohort(
            cohort_id="c42",
            master_id="m1",
            module_id="mod99",
        )
        assert cohort.cohort_id == "c42"
        assert cohort.master_id == "m1"
        assert cohort.module_id == "mod99"

    def test_starts_with_no_memberships(self) -> None:
        cohort = make_cohort()
        assert cohort.memberships == []

    def test_sets_formed_at_timestamp(self) -> None:
        before = datetime.now(timezone.utc)
        cohort = make_cohort()
        after = datetime.now(timezone.utc)
        assert before <= cohort.formed_at <= after

    def test_emits_cohort_formed_event(self) -> None:
        cohort = make_cohort(cohort_id="c1", master_id="m1", module_id="mod1")
        events = cohort.collect_events()
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, CohortFormed)
        assert event.cohort_id == "c1"
        assert event.master_id == "m1"
        assert event.module_id == "mod1"

    def test_collect_events_clears_events(self) -> None:
        cohort = make_cohort()
        cohort.collect_events()
        assert cohort.collect_events() == []


# =============================================================================
# Learner enrollment
# =============================================================================


class TestEnrolLearner:
    def test_enrols_learner_with_learner_role(self) -> None:
        cohort = make_cohort()
        cohort.enrol_learner(membership_id="mem1", learner_id="l1")
        assert len(cohort.memberships) == 1
        m = cohort.memberships[0]
        assert m.learner_id == "l1"
        assert m.role == CohortRole.LEARNER
        assert m.is_active is True

    def test_enrol_emits_learner_enrolled_event(self) -> None:
        cohort = make_cohort(cohort_id="c1")
        cohort.collect_events()  # clear CohortFormed
        cohort.enrol_learner(membership_id="mem1", learner_id="l1")
        events = cohort.collect_events()
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, LearnerEnrolled)
        assert event.cohort_id == "c1"
        assert event.membership_id == "mem1"
        assert event.learner_id == "l1"

    def test_cannot_enrol_same_learner_twice(self) -> None:
        cohort = make_cohort()
        cohort.enrol_learner(membership_id="mem1", learner_id="l1")
        with pytest.raises(ValueError, match="already enrolled"):
            cohort.enrol_learner(membership_id="mem2", learner_id="l1")

    def test_cannot_enrol_the_master(self) -> None:
        cohort = make_cohort(master_id="m1")
        with pytest.raises(ValueError, match="[Mm]aster"):
            cohort.enrol_learner(membership_id="mem1", learner_id="m1")

    def test_cannot_enrol_beyond_max_learners(self) -> None:
        cohort = make_cohort()
        for i in range(15):
            cohort.enrol_learner(membership_id=f"mem{i}", learner_id=f"l{i}")
        with pytest.raises(ValueError, match="maximum"):
            cohort.enrol_learner(membership_id="mem_over", learner_id="l_over")

    def test_cannot_enrol_in_non_forming_status(self) -> None:
        cohort = make_active_cohort()
        with pytest.raises(ValueError, match="[Ff]orming"):
            cohort.enrol_learner(membership_id="mem_new", learner_id="l_new")


# =============================================================================
# Learner removal
# =============================================================================


class TestRemoveLearner:
    def test_removes_learner_by_membership_id(self) -> None:
        cohort = make_cohort()
        cohort.enrol_learner(membership_id="mem1", learner_id="l1")
        cohort.collect_events()
        cohort.remove_learner("mem1")
        m = cohort.memberships[0]
        assert m.is_active is False

    def test_remove_emits_learner_removed_event(self) -> None:
        cohort = make_cohort(cohort_id="c1")
        cohort.enrol_learner(membership_id="mem1", learner_id="l1")
        cohort.collect_events()
        cohort.remove_learner("mem1")
        events = cohort.collect_events()
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, LearnerRemoved)
        assert event.cohort_id == "c1"
        assert event.membership_id == "mem1"
        assert event.learner_id == "l1"

    def test_cannot_remove_nonexistent_membership(self) -> None:
        cohort = make_cohort()
        with pytest.raises(LookupError, match="not found"):
            cohort.remove_learner("nonexistent")

    def test_cannot_remove_already_inactive_membership(self) -> None:
        cohort = make_cohort()
        cohort.enrol_learner(membership_id="mem1", learner_id="l1")
        cohort.remove_learner("mem1")
        with pytest.raises(ValueError, match="already inactive"):
            cohort.remove_learner("mem1")


# =============================================================================
# Status transitions
# =============================================================================


class TestCohortActivation:
    def test_activate_transitions_to_active(self) -> None:
        cohort = make_cohort()
        for i in range(5):
            cohort.enrol_learner(membership_id=f"mem{i}", learner_id=f"l{i}")
        cohort.activate()
        assert cohort.status == CohortStatus.ACTIVE

    def test_activate_emits_cohort_activated_event(self) -> None:
        cohort = make_cohort(cohort_id="c1")
        for i in range(5):
            cohort.enrol_learner(membership_id=f"mem{i}", learner_id=f"l{i}")
        cohort.collect_events()
        cohort.activate()
        events = cohort.collect_events()
        assert any(
            isinstance(e, CohortActivated) and e.cohort_id == "c1" for e in events
        )

    def test_cannot_activate_with_fewer_than_min_learners(self) -> None:
        cohort = make_cohort()
        cohort.enrol_learner(membership_id="mem1", learner_id="l1")
        with pytest.raises(ValueError, match="minimum"):
            cohort.activate()

    def test_cannot_activate_from_active_status(self) -> None:
        cohort = make_active_cohort()
        with pytest.raises(ValueError, match="[Cc]annot transition"):
            cohort.activate()


class TestCohortCompletion:
    def test_begin_completing_transitions_to_completing(self) -> None:
        cohort = make_active_cohort()
        cohort.begin_completing()
        assert cohort.status == CohortStatus.COMPLETING

    def test_graduate_transitions_to_graduated(self) -> None:
        cohort = make_active_cohort()
        cohort.begin_completing()
        cohort.graduate()
        assert cohort.status == CohortStatus.GRADUATED

    def test_graduate_emits_cohort_graduated_event(self) -> None:
        cohort = make_active_cohort(cohort_id="c1")
        cohort.begin_completing()
        cohort.collect_events()
        cohort.graduate()
        events = cohort.collect_events()
        assert any(
            isinstance(e, CohortGraduated) and e.cohort_id == "c1" for e in events
        )

    def test_graduated_is_terminal(self) -> None:
        cohort = make_active_cohort()
        cohort.begin_completing()
        cohort.graduate()
        with pytest.raises(ValueError, match="[Cc]annot transition"):
            cohort.cancel()


class TestCohortCancellation:
    def test_cancel_from_forming(self) -> None:
        cohort = make_cohort()
        cohort.cancel()
        assert cohort.status == CohortStatus.CANCELLED

    def test_cancel_from_active(self) -> None:
        cohort = make_active_cohort()
        cohort.cancel()
        assert cohort.status == CohortStatus.CANCELLED

    def test_cancel_emits_cohort_cancelled_event(self) -> None:
        cohort = make_cohort(cohort_id="c1")
        cohort.collect_events()
        cohort.cancel()
        events = cohort.collect_events()
        assert any(
            isinstance(e, CohortCancelled) and e.cohort_id == "c1" for e in events
        )

    def test_cancelled_is_terminal(self) -> None:
        cohort = make_cohort()
        cohort.cancel()
        with pytest.raises(ValueError, match="[Cc]annot transition"):
            cohort.activate()


# =============================================================================
# Queries
# =============================================================================


class TestCohortQueries:
    def test_active_learner_count(self) -> None:
        cohort = make_cohort()
        cohort.enrol_learner(membership_id="mem1", learner_id="l1")
        cohort.enrol_learner(membership_id="mem2", learner_id="l2")
        assert cohort.active_learner_count == 2

    def test_active_learner_count_excludes_removed(self) -> None:
        cohort = make_cohort()
        cohort.enrol_learner(membership_id="mem1", learner_id="l1")
        cohort.enrol_learner(membership_id="mem2", learner_id="l2")
        cohort.remove_learner("mem1")
        assert cohort.active_learner_count == 1

    def test_find_membership_by_learner_id(self) -> None:
        cohort = make_cohort()
        cohort.enrol_learner(membership_id="mem1", learner_id="l1")
        m = cohort.find_membership_by_learner_id("l1")
        assert m is not None
        assert m.membership_id == "mem1"

    def test_find_membership_returns_none_for_unknown(self) -> None:
        cohort = make_cohort()
        assert cohort.find_membership_by_learner_id("unknown") is None

    def test_find_membership_returns_none_for_inactive(self) -> None:
        cohort = make_cohort()
        cohort.enrol_learner(membership_id="mem1", learner_id="l1")
        cohort.remove_learner("mem1")
        assert cohort.find_membership_by_learner_id("l1") is None
