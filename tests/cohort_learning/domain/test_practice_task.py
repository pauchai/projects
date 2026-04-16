"""Tests for PracticeTask aggregate root."""

import pytest

from cohort_learning.domain.events import (
    PracticeTaskCreated,
    TaskSubmissionCreated,
)
from cohort_learning.domain.practice_task import PracticeTask
from cohort_learning.domain.task_status import SubmissionStatus, TaskStatus


class TestPracticeTaskCreation:
    """PracticeTask is an aggregate root for tasks within a cohort."""

    def test_stores_task_id(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        assert task.task_id == "task1"

    def test_stores_cohort_id(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        assert task.cohort_id == "c1"

    def test_stores_topic_id(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        assert task.topic_id == "t1"

    def test_stores_creator_id(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        assert task.creator_id == "master1"

    def test_stores_title(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        assert task.title == "Build a REST API"

    def test_description_defaults_to_empty(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        assert task.description == ""

    def test_stores_description(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
            description="Create CRUD endpoints",
        )
        assert task.description == "Create CRUD endpoints"

    def test_default_status_is_draft(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        assert task.status == TaskStatus.DRAFT

    def test_created_at_is_set(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        assert task.created_at is not None

    def test_submissions_initially_empty(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        assert task.submissions == []

    def test_emits_practice_task_created_event(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        events = task.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], PracticeTaskCreated)
        assert events[0].task_id == "task1"
        assert events[0].cohort_id == "c1"
        assert events[0].topic_id == "t1"
        assert events[0].creator_id == "master1"
        assert events[0].title == "Build a REST API"


class TestPracticeTaskValidation:
    """PracticeTask rejects invalid inputs."""

    def test_raises_on_empty_title(self) -> None:
        with pytest.raises(ValueError, match="title"):
            PracticeTask(
                task_id="task1",
                cohort_id="c1",
                topic_id="t1",
                creator_id="master1",
                title="",
            )

    def test_raises_on_whitespace_title(self) -> None:
        with pytest.raises(ValueError, match="title"):
            PracticeTask(
                task_id="task1",
                cohort_id="c1",
                topic_id="t1",
                creator_id="master1",
                title="   ",
            )


class TestPracticeTaskStatusTransitions:
    """Task follows Draft -> Active -> Closed lifecycle."""

    def test_activate_transitions_to_active(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        task.activate()
        assert task.status == TaskStatus.ACTIVE

    def test_close_transitions_from_active(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        task.activate()
        task.close()
        assert task.status == TaskStatus.CLOSED

    def test_close_transitions_from_draft(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        task.close()
        assert task.status == TaskStatus.CLOSED

    def test_activate_raises_from_closed(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        task.close()
        with pytest.raises(ValueError, match="Cannot transition"):
            task.activate()


class TestPracticeTaskSubmissions:
    """PracticeTask manages learner submissions."""

    def test_add_submission_stores_submission(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        task.activate()
        task.collect_events()

        task.add_submission(
            submission_id="sub1",
            learner_id="learner1",
            content="My solution",
        )
        assert len(task.submissions) == 1
        assert task.submissions[0].submission_id == "sub1"
        assert task.submissions[0].learner_id == "learner1"

    def test_add_submission_emits_event(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        task.activate()
        task.collect_events()

        task.add_submission(
            submission_id="sub1",
            learner_id="learner1",
            content="My solution",
        )
        events = task.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], TaskSubmissionCreated)
        assert events[0].submission_id == "sub1"
        assert events[0].task_id == "task1"
        assert events[0].learner_id == "learner1"
        assert events[0].cohort_id == "c1"

    def test_add_submission_raises_when_task_not_active(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        with pytest.raises(ValueError, match="only.*active"):
            task.add_submission(
                submission_id="sub1",
                learner_id="learner1",
                content="My solution",
            )

    def test_add_submission_raises_when_task_closed(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        task.close()
        with pytest.raises(ValueError, match="only.*active"):
            task.add_submission(
                submission_id="sub1",
                learner_id="learner1",
                content="My solution",
            )

    def test_add_submission_raises_when_creator_submits(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        task.activate()
        with pytest.raises(ValueError, match="creator"):
            task.add_submission(
                submission_id="sub1",
                learner_id="master1",
                content="My solution",
            )

    def test_add_submission_raises_on_duplicate_learner(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        task.activate()
        task.add_submission(
            submission_id="sub1",
            learner_id="learner1",
            content="First attempt",
        )
        with pytest.raises(ValueError, match="already submitted"):
            task.add_submission(
                submission_id="sub2",
                learner_id="learner1",
                content="Second attempt",
            )

    def test_multiple_learners_can_submit(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        task.activate()
        task.add_submission(
            submission_id="sub1",
            learner_id="learner1",
            content="Solution A",
        )
        task.add_submission(
            submission_id="sub2",
            learner_id="learner2",
            content="Solution B",
        )
        assert len(task.submissions) == 2

    def test_learner_can_resubmit_after_revision_requested(self) -> None:
        """After revision requested, the same learner's submission can be resubmitted."""
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        task.activate()
        task.add_submission(
            submission_id="sub1",
            learner_id="learner1",
            content="First attempt",
        )
        # Simulate review workflow on the submission
        sub = task.submissions[0]
        sub.begin_review()
        sub.request_revision()
        sub.resubmit("Improved attempt")
        assert sub.content == "Improved attempt"
        assert sub.status == SubmissionStatus.SUBMITTED


class TestPracticeTaskQueries:
    """PracticeTask provides query methods for submissions."""

    def test_find_submission_by_id(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        task.activate()
        task.add_submission(
            submission_id="sub1",
            learner_id="learner1",
            content="My solution",
        )
        found = task.find_submission("sub1")
        assert found is not None
        assert found.submission_id == "sub1"

    def test_find_submission_returns_none_when_not_found(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        assert task.find_submission("nonexistent") is None

    def test_find_submission_by_learner(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        task.activate()
        task.add_submission(
            submission_id="sub1",
            learner_id="learner1",
            content="My solution",
        )
        found = task.find_submission_by_learner("learner1")
        assert found is not None
        assert found.learner_id == "learner1"

    def test_find_submission_by_learner_returns_none(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        assert task.find_submission_by_learner("unknown") is None

    def test_submission_count(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        task.activate()
        assert task.submission_count == 0
        task.add_submission(
            submission_id="sub1",
            learner_id="learner1",
            content="Solution",
        )
        assert task.submission_count == 1


class TestPracticeTaskCollectEvents:
    """PracticeTask collects and clears events like other aggregates."""

    def test_collect_events_returns_and_clears(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        events = task.collect_events()
        assert len(events) == 1
        # Second call returns empty
        assert task.collect_events() == []

    def test_events_accumulate_across_operations(self) -> None:
        task = PracticeTask(
            task_id="task1",
            cohort_id="c1",
            topic_id="t1",
            creator_id="master1",
            title="Build a REST API",
        )
        task.activate()
        task.add_submission(
            submission_id="sub1",
            learner_id="learner1",
            content="My solution",
        )
        events = task.collect_events()
        # PracticeTaskCreated + TaskSubmissionCreated
        assert len(events) == 2
        assert isinstance(events[0], PracticeTaskCreated)
        assert isinstance(events[1], TaskSubmissionCreated)
