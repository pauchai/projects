"""Tests for TaskSubmission entity."""

import pytest

from cohort_learning.domain.task_submission import TaskSubmission
from cohort_learning.domain.task_status import SubmissionStatus


class TestTaskSubmissionCreation:
    """TaskSubmission records a learner's solution for a practice task."""

    def test_stores_submission_id(self) -> None:
        sub = TaskSubmission(
            submission_id="sub1",
            task_id="task1",
            learner_id="learner1",
            content="My solution",
        )
        assert sub.submission_id == "sub1"

    def test_stores_task_id(self) -> None:
        sub = TaskSubmission(
            submission_id="sub1",
            task_id="task1",
            learner_id="learner1",
            content="My solution",
        )
        assert sub.task_id == "task1"

    def test_stores_learner_id(self) -> None:
        sub = TaskSubmission(
            submission_id="sub1",
            task_id="task1",
            learner_id="learner1",
            content="My solution",
        )
        assert sub.learner_id == "learner1"

    def test_stores_content(self) -> None:
        sub = TaskSubmission(
            submission_id="sub1",
            task_id="task1",
            learner_id="learner1",
            content="My solution",
        )
        assert sub.content == "My solution"

    def test_default_status_is_submitted(self) -> None:
        sub = TaskSubmission(
            submission_id="sub1",
            task_id="task1",
            learner_id="learner1",
            content="My solution",
        )
        assert sub.status == SubmissionStatus.SUBMITTED

    def test_submitted_at_is_set(self) -> None:
        sub = TaskSubmission(
            submission_id="sub1",
            task_id="task1",
            learner_id="learner1",
            content="My solution",
        )
        assert sub.submitted_at is not None


class TestTaskSubmissionValidation:
    """TaskSubmission rejects invalid inputs."""

    def test_raises_on_empty_content(self) -> None:
        with pytest.raises(ValueError, match="content"):
            TaskSubmission(
                submission_id="sub1",
                task_id="task1",
                learner_id="learner1",
                content="",
            )

    def test_raises_on_whitespace_content(self) -> None:
        with pytest.raises(ValueError, match="content"):
            TaskSubmission(
                submission_id="sub1",
                task_id="task1",
                learner_id="learner1",
                content="   ",
            )


class TestTaskSubmissionStatusTransitions:
    """Submission status follows a strict workflow."""

    def test_begin_review_transitions_to_in_review(self) -> None:
        sub = TaskSubmission(
            submission_id="sub1",
            task_id="task1",
            learner_id="learner1",
            content="My solution",
        )
        sub.begin_review()
        assert sub.status == SubmissionStatus.IN_REVIEW

    def test_approve_transitions_from_in_review_to_approved(self) -> None:
        sub = TaskSubmission(
            submission_id="sub1",
            task_id="task1",
            learner_id="learner1",
            content="My solution",
        )
        sub.begin_review()
        sub.approve()
        assert sub.status == SubmissionStatus.APPROVED

    def test_request_revision_transitions_from_in_review(self) -> None:
        sub = TaskSubmission(
            submission_id="sub1",
            task_id="task1",
            learner_id="learner1",
            content="My solution",
        )
        sub.begin_review()
        sub.request_revision()
        assert sub.status == SubmissionStatus.REVISION_REQUESTED

    def test_resubmit_transitions_from_revision_requested(self) -> None:
        sub = TaskSubmission(
            submission_id="sub1",
            task_id="task1",
            learner_id="learner1",
            content="My solution",
        )
        sub.begin_review()
        sub.request_revision()
        sub.resubmit("Updated solution")
        assert sub.status == SubmissionStatus.SUBMITTED
        assert sub.content == "Updated solution"

    def test_approve_raises_from_submitted(self) -> None:
        sub = TaskSubmission(
            submission_id="sub1",
            task_id="task1",
            learner_id="learner1",
            content="My solution",
        )
        with pytest.raises(ValueError, match="Cannot transition"):
            sub.approve()

    def test_resubmit_raises_from_submitted(self) -> None:
        sub = TaskSubmission(
            submission_id="sub1",
            task_id="task1",
            learner_id="learner1",
            content="My solution",
        )
        with pytest.raises(ValueError, match="Cannot transition"):
            sub.resubmit("New content")

    def test_resubmit_raises_on_empty_content(self) -> None:
        sub = TaskSubmission(
            submission_id="sub1",
            task_id="task1",
            learner_id="learner1",
            content="My solution",
        )
        sub.begin_review()
        sub.request_revision()
        with pytest.raises(ValueError, match="content"):
            sub.resubmit("")
