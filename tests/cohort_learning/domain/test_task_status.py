"""Tests for task-related status enums."""

import pytest

from cohort_learning.domain.task_status import (
    SubmissionStatus,
    TaskStatus,
)


class TestTaskStatus:
    """TaskStatus represents the lifecycle of a practice task."""

    def test_draft_is_default_initial_status(self) -> None:
        assert TaskStatus.DRAFT.value == "draft"

    def test_active_status(self) -> None:
        assert TaskStatus.ACTIVE.value == "active"

    def test_closed_status(self) -> None:
        assert TaskStatus.CLOSED.value == "closed"

    def test_draft_can_transition_to_active(self) -> None:
        assert TaskStatus.DRAFT.can_transition_to(TaskStatus.ACTIVE) is True

    def test_draft_can_transition_to_closed(self) -> None:
        assert TaskStatus.DRAFT.can_transition_to(TaskStatus.CLOSED) is True

    def test_active_can_transition_to_closed(self) -> None:
        assert TaskStatus.ACTIVE.can_transition_to(TaskStatus.CLOSED) is True

    def test_active_cannot_transition_to_draft(self) -> None:
        assert TaskStatus.ACTIVE.can_transition_to(TaskStatus.DRAFT) is False

    def test_closed_cannot_transition_anywhere(self) -> None:
        assert TaskStatus.CLOSED.can_transition_to(TaskStatus.DRAFT) is False
        assert TaskStatus.CLOSED.can_transition_to(TaskStatus.ACTIVE) is False

    def test_same_status_transition_is_rejected(self) -> None:
        assert TaskStatus.ACTIVE.can_transition_to(TaskStatus.ACTIVE) is False


class TestSubmissionStatus:
    """SubmissionStatus tracks a learner's task submission lifecycle."""

    def test_submitted_status(self) -> None:
        assert SubmissionStatus.SUBMITTED.value == "submitted"

    def test_in_review_status(self) -> None:
        assert SubmissionStatus.IN_REVIEW.value == "in_review"

    def test_approved_status(self) -> None:
        assert SubmissionStatus.APPROVED.value == "approved"

    def test_revision_requested_status(self) -> None:
        assert SubmissionStatus.REVISION_REQUESTED.value == "revision_requested"

    def test_submitted_can_transition_to_in_review(self) -> None:
        assert (
            SubmissionStatus.SUBMITTED.can_transition_to(SubmissionStatus.IN_REVIEW)
            is True
        )

    def test_in_review_can_transition_to_approved(self) -> None:
        assert (
            SubmissionStatus.IN_REVIEW.can_transition_to(SubmissionStatus.APPROVED)
            is True
        )

    def test_in_review_can_transition_to_revision_requested(self) -> None:
        assert (
            SubmissionStatus.IN_REVIEW.can_transition_to(
                SubmissionStatus.REVISION_REQUESTED
            )
            is True
        )

    def test_revision_requested_can_transition_to_submitted(self) -> None:
        assert (
            SubmissionStatus.REVISION_REQUESTED.can_transition_to(
                SubmissionStatus.SUBMITTED
            )
            is True
        )

    def test_approved_is_terminal(self) -> None:
        for status in SubmissionStatus:
            if status != SubmissionStatus.APPROVED:
                assert SubmissionStatus.APPROVED.can_transition_to(status) is False

    def test_submitted_cannot_jump_to_approved(self) -> None:
        assert (
            SubmissionStatus.SUBMITTED.can_transition_to(SubmissionStatus.APPROVED)
            is False
        )

    def test_same_status_transition_is_rejected(self) -> None:
        assert (
            SubmissionStatus.SUBMITTED.can_transition_to(SubmissionStatus.SUBMITTED)
            is False
        )
