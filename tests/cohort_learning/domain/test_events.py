"""Tests for domain event dataclasses."""

import pytest
from dataclasses import FrozenInstanceError

from cohort_learning.domain.cohort_role import CohortRole
from shared_kernel.events import DomainEvent


class TestDomainEventBase:
    """All events inherit from DomainEvent and are frozen."""

    def test_cohort_formed_is_domain_event(self) -> None:
        from cohort_learning.domain.events import CohortFormed

        event = CohortFormed(cohort_id="c1", master_id="m1", module_id="mod1")
        assert isinstance(event, DomainEvent)

    def test_events_are_frozen(self) -> None:
        from cohort_learning.domain.events import CohortFormed

        event = CohortFormed(cohort_id="c1", master_id="m1", module_id="mod1")
        with pytest.raises(FrozenInstanceError):
            event.cohort_id = "c2"  # type: ignore[misc]


class TestCohortLifecycleEvents:
    """Cohort lifecycle events carry the correct payloads."""

    def test_cohort_formed_fields(self) -> None:
        from cohort_learning.domain.events import CohortFormed

        event = CohortFormed(cohort_id="c1", master_id="m1", module_id="mod1")
        assert event.cohort_id == "c1"
        assert event.master_id == "m1"
        assert event.module_id == "mod1"

    def test_cohort_activated_fields(self) -> None:
        from cohort_learning.domain.events import CohortActivated

        event = CohortActivated(cohort_id="c1")
        assert event.cohort_id == "c1"

    def test_cohort_graduated_fields(self) -> None:
        from cohort_learning.domain.events import CohortGraduated

        event = CohortGraduated(cohort_id="c1")
        assert event.cohort_id == "c1"

    def test_cohort_cancelled_fields(self) -> None:
        from cohort_learning.domain.events import CohortCancelled

        event = CohortCancelled(cohort_id="c1")
        assert event.cohort_id == "c1"


class TestMembershipEvents:
    """Membership events carry membership, cohort, and user details."""

    def test_learner_enrolled_fields(self) -> None:
        from cohort_learning.domain.events import LearnerEnrolled

        event = LearnerEnrolled(cohort_id="c1", membership_id="mem1", learner_id="u1")
        assert event.cohort_id == "c1"
        assert event.membership_id == "mem1"
        assert event.learner_id == "u1"

    def test_learner_removed_fields(self) -> None:
        from cohort_learning.domain.events import LearnerRemoved

        event = LearnerRemoved(cohort_id="c1", membership_id="mem1", learner_id="u1")
        assert event.cohort_id == "c1"
        assert event.membership_id == "mem1"
        assert event.learner_id == "u1"


class TestProgressionEvents:
    """Role promotion events carry cohort, user, and role details."""

    def test_topic_expert_promoted_fields(self) -> None:
        from cohort_learning.domain.events import TopicExpertPromoted

        event = TopicExpertPromoted(cohort_id="c1", learner_id="u1", topic_id="t1")
        assert event.cohort_id == "c1"
        assert event.learner_id == "u1"
        assert event.topic_id == "t1"

    def test_curator_promoted_fields(self) -> None:
        from cohort_learning.domain.events import CuratorPromoted

        event = CuratorPromoted(cohort_id="c1", learner_id="u1", module_id="mod1")
        assert event.cohort_id == "c1"
        assert event.learner_id == "u1"
        assert event.module_id == "mod1"


class TestCompetencyEvents:
    """Competency and task events."""

    def test_topic_competency_achieved_fields(self) -> None:
        from cohort_learning.domain.events import TopicCompetencyAchieved

        event = TopicCompetencyAchieved(cohort_id="c1", learner_id="u1", topic_id="t1")
        assert event.cohort_id == "c1"
        assert event.learner_id == "u1"
        assert event.topic_id == "t1"

    def test_practice_task_completed_fields(self) -> None:
        from cohort_learning.domain.events import PracticeTaskCompleted

        event = PracticeTaskCompleted(
            cohort_id="c1", learner_id="u1", task_id="task1", topic_id="t1"
        )
        assert event.cohort_id == "c1"
        assert event.learner_id == "u1"
        assert event.task_id == "task1"
        assert event.topic_id == "t1"
