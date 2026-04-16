"""Tests for CompetencyAchievementSaga (Stage 14).

Tests verify that the saga correctly detects when a learner has completed all
tasks and received at least 2 peer reviews for a topic, emitting
``CompetencyPrerequisitesMet`` when both conditions are satisfied.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cohort_learning.application.sagas.competency_achievement_saga import (
    CompetencyAchievementSaga,
)
from cohort_learning.domain.events import (
    CompetencyPrerequisitesMet,
    PeerReviewSubmitted,
)
from cohort_learning.domain.topic_competency import TopicCompetency
from tests.cohort_learning.factories import (
    make_active_task,
    make_review,
    make_task,
    save_review,
    save_task,
)
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork


def _make_event(
    submission_id: str = "sub1",
    task_id: str = "task1",
    cohort_id: str = "c1",
    reviewer_id: str = "reviewer1",
    review_id: str = "rev1",
) -> PeerReviewSubmitted:
    return PeerReviewSubmitted(
        review_id=review_id,
        submission_id=submission_id,
        reviewer_id=reviewer_id,
        task_id=task_id,
        cohort_id=cohort_id,
    )


def _make_submitted_review(**overrides: object) -> object:
    """Return a fully submitted PeerReview with one score attached."""
    from cohort_learning.domain.review_score import ReviewScore

    review = make_review(**overrides)
    review.submit([ReviewScore(criterion="quality", score=4)])
    review.collect_events()  # clear events
    return review


class TestCompetencyAchievementSagaDoesNothing:
    """Saga silently skips when prerequisites are not fully met."""

    def test_does_nothing_when_task_not_found(self) -> None:
        bus = MagicMock()
        uow = FakeUnitOfWork()
        saga = CompetencyAchievementSaga(uow=uow, event_bus=bus)

        saga.handle(_make_event(task_id="nonexistent"))

        bus.publish.assert_not_called()

    def test_does_nothing_when_submission_not_in_task(self) -> None:
        bus = MagicMock()
        uow = FakeUnitOfWork()
        # task exists but has no submissions
        task = make_active_task(task_id="task1", topic_id="t1", cohort_id="c1")
        save_task(uow, task)
        saga = CompetencyAchievementSaga(uow=uow, event_bus=bus)

        saga.handle(_make_event(task_id="task1", submission_id="unknown_sub"))

        bus.publish.assert_not_called()

    def test_does_nothing_when_no_tasks_for_topic(self) -> None:
        """Even if the task/submission exist, topic has no tasks → no prereqs."""
        bus = MagicMock()
        uow = FakeUnitOfWork()
        # We only save a DRAFT task (not found via find_by_cohort filtering for topic).
        # Instead, make an active task on a DIFFERENT topic so the learner's topic is empty.
        task = make_active_task(task_id="task1", topic_id="other_topic", cohort_id="c1")
        task.add_submission(submission_id="sub1", learner_id="learner1", content="Work")
        save_task(uow, task)
        # Now fire an event for task1 whose topic_id would be "other_topic"
        # but build a separate task with topic_id="t1" that has no tasks at all.
        task2 = make_active_task(task_id="task2", topic_id="t1", cohort_id="c1")
        task2.add_submission(submission_id="sub2", learner_id="learner1", content="X")
        save_task(uow, task2)

        # Event refers to task2 / sub2 - topic t1 has exactly 1 task (task2)
        # learner1 has submitted, but no reviews yet → condition 2 fails.
        saga = CompetencyAchievementSaga(uow=uow, event_bus=bus)
        saga.handle(_make_event(task_id="task2", submission_id="sub2"))

        bus.publish.assert_not_called()

    def test_does_nothing_when_not_all_tasks_completed(self) -> None:
        """Learner has submitted to some but not all tasks in the topic."""
        bus = MagicMock()
        uow = FakeUnitOfWork()

        task1 = make_active_task(task_id="task1", topic_id="t1", cohort_id="c1")
        task1.add_submission(submission_id="sub1", learner_id="learner1", content="A")

        task2 = make_active_task(task_id="task2", topic_id="t1", cohort_id="c1")
        # learner1 has NOT submitted to task2

        save_task(uow, task1)
        save_task(uow, task2)

        # Enough reviews for sub1
        for i in range(2):
            r = _make_submitted_review(
                review_id=f"rev{i}",
                submission_id="sub1",
                reviewer_id=f"rev{i}",
                task_id="task1",
                cohort_id="c1",
            )
            save_review(uow, r)

        saga = CompetencyAchievementSaga(uow=uow, event_bus=bus)
        saga.handle(_make_event(task_id="task1", submission_id="sub1"))

        bus.publish.assert_not_called()

    def test_does_nothing_when_only_one_review_received(self) -> None:
        """Exactly 1 review received — minimum is 2."""
        bus = MagicMock()
        uow = FakeUnitOfWork()

        task = make_active_task(task_id="task1", topic_id="t1", cohort_id="c1")
        task.add_submission(submission_id="sub1", learner_id="learner1", content="A")
        save_task(uow, task)

        r = _make_submitted_review(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="reviewer2",
            task_id="task1",
            cohort_id="c1",
        )
        save_review(uow, r)

        saga = CompetencyAchievementSaga(uow=uow, event_bus=bus)
        saga.handle(_make_event(task_id="task1", submission_id="sub1"))

        bus.publish.assert_not_called()

    def test_does_nothing_when_zero_reviews_received(self) -> None:
        bus = MagicMock()
        uow = FakeUnitOfWork()

        task = make_active_task(task_id="task1", topic_id="t1", cohort_id="c1")
        task.add_submission(submission_id="sub1", learner_id="learner1", content="A")
        save_task(uow, task)

        saga = CompetencyAchievementSaga(uow=uow, event_bus=bus)
        saga.handle(_make_event(task_id="task1", submission_id="sub1"))

        bus.publish.assert_not_called()

    def test_does_nothing_when_already_competent(self) -> None:
        """Idempotency: skip if TopicCompetency already exists for this learner/topic."""
        bus = MagicMock()
        uow = FakeUnitOfWork()

        task = make_active_task(task_id="task1", topic_id="t1", cohort_id="c1")
        task.add_submission(submission_id="sub1", learner_id="learner1", content="A")
        save_task(uow, task)

        for i in range(2):
            r = _make_submitted_review(
                review_id=f"rev{i}",
                submission_id="sub1",
                reviewer_id=f"reviewer{i}",
                task_id="task1",
                cohort_id="c1",
            )
            save_review(uow, r)

        # Learner already validated
        with uow:
            uow.topic_competencies.save(
                TopicCompetency(
                    competency_id="comp1",
                    learner_id="learner1",
                    topic_id="t1",
                    cohort_id="c1",
                )
            )
            uow.commit()

        saga = CompetencyAchievementSaga(uow=uow, event_bus=bus)
        saga.handle(_make_event(task_id="task1", submission_id="sub1"))

        bus.publish.assert_not_called()


class TestCompetencyAchievementSagaEmitsEvent:
    """Saga emits CompetencyPrerequisitesMet when all conditions are met."""

    def test_emits_prerequisites_met_on_happy_path(self) -> None:
        """Single task, 2 reviews — both conditions met."""
        bus = MagicMock()
        uow = FakeUnitOfWork()

        task = make_active_task(task_id="task1", topic_id="t1", cohort_id="c1")
        task.add_submission(submission_id="sub1", learner_id="learner1", content="A")
        save_task(uow, task)

        for i in range(2):
            r = _make_submitted_review(
                review_id=f"rev{i}",
                submission_id="sub1",
                reviewer_id=f"reviewer{i}",
                task_id="task1",
                cohort_id="c1",
            )
            save_review(uow, r)

        saga = CompetencyAchievementSaga(uow=uow, event_bus=bus)
        saga.handle(_make_event(task_id="task1", submission_id="sub1"))

        bus.publish.assert_called_once()
        events = bus.publish.call_args[0][0]
        assert len(events) == 1
        evt = events[0]
        assert isinstance(evt, CompetencyPrerequisitesMet)
        assert evt.learner_id == "learner1"
        assert evt.topic_id == "t1"
        assert evt.cohort_id == "c1"

    def test_emits_with_more_than_2_reviews(self) -> None:
        """3 reviews is still eligible."""
        bus = MagicMock()
        uow = FakeUnitOfWork()

        task = make_active_task(task_id="task1", topic_id="t1", cohort_id="c1")
        task.add_submission(submission_id="sub1", learner_id="learner1", content="A")
        save_task(uow, task)

        for i in range(3):
            r = _make_submitted_review(
                review_id=f"rev{i}",
                submission_id="sub1",
                reviewer_id=f"reviewer{i}",
                task_id="task1",
                cohort_id="c1",
            )
            save_review(uow, r)

        saga = CompetencyAchievementSaga(uow=uow, event_bus=bus)
        saga.handle(_make_event(task_id="task1", submission_id="sub1"))

        bus.publish.assert_called_once()

    def test_counts_reviews_across_multiple_tasks_in_same_topic(self) -> None:
        """Reviews on different tasks for the same topic all count."""
        bus = MagicMock()
        uow = FakeUnitOfWork()

        task1 = make_active_task(task_id="task1", topic_id="t1", cohort_id="c1")
        task1.add_submission(submission_id="sub1", learner_id="learner1", content="A")

        task2 = make_active_task(task_id="task2", topic_id="t1", cohort_id="c1")
        task2.add_submission(submission_id="sub2", learner_id="learner1", content="B")

        save_task(uow, task1)
        save_task(uow, task2)

        # 1 review on sub1, 1 review on sub2 → total = 2
        r1 = _make_submitted_review(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="reviewer1",
            task_id="task1",
            cohort_id="c1",
        )
        r2 = _make_submitted_review(
            review_id="rev2",
            submission_id="sub2",
            reviewer_id="reviewer2",
            task_id="task2",
            cohort_id="c1",
        )
        save_review(uow, r1)
        save_review(uow, r2)

        saga = CompetencyAchievementSaga(uow=uow, event_bus=bus)
        # Event from reviewing sub2 on task2
        saga.handle(_make_event(task_id="task2", submission_id="sub2"))

        bus.publish.assert_called_once()
        events = bus.publish.call_args[0][0]
        assert isinstance(events[0], CompetencyPrerequisitesMet)
        assert events[0].learner_id == "learner1"

    def test_only_checks_topic_of_triggering_task(self) -> None:
        """Reviews on a different topic do not satisfy this topic's prerequisites."""
        bus = MagicMock()
        uow = FakeUnitOfWork()

        # t1 task with 2 reviews — will be eligible
        t1_task = make_active_task(task_id="task1", topic_id="t1", cohort_id="c1")
        t1_task.add_submission(submission_id="sub1", learner_id="learner1", content="A")
        save_task(uow, t1_task)

        for i in range(2):
            r = _make_submitted_review(
                review_id=f"rev{i}",
                submission_id="sub1",
                reviewer_id=f"reviewer{i}",
                task_id="task1",
                cohort_id="c1",
            )
            save_review(uow, r)

        # t2 task with only 1 review — NOT eligible
        t2_task = make_active_task(task_id="task2", topic_id="t2", cohort_id="c1")
        t2_task.add_submission(submission_id="sub2", learner_id="learner1", content="B")
        save_task(uow, t2_task)
        r_t2 = _make_submitted_review(
            review_id="rev_t2",
            submission_id="sub2",
            reviewer_id="reviewer99",
            task_id="task2",
            cohort_id="c1",
        )
        save_review(uow, r_t2)

        saga = CompetencyAchievementSaga(uow=uow, event_bus=bus)
        # Event from t2 review — should NOT be eligible (only 1 review for t2)
        saga.handle(_make_event(task_id="task2", submission_id="sub2"))

        bus.publish.assert_not_called()
