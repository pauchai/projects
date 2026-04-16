"""Tests for ReviewStatus enum."""

import pytest

from cohort_learning.domain.review_status import ReviewStatus


class TestReviewStatus:
    """ReviewStatus tracks the lifecycle of a peer review."""

    def test_draft_status(self) -> None:
        assert ReviewStatus.DRAFT.value == "draft"

    def test_submitted_status(self) -> None:
        assert ReviewStatus.SUBMITTED.value == "submitted"

    def test_draft_can_transition_to_submitted(self) -> None:
        assert ReviewStatus.DRAFT.can_transition_to(ReviewStatus.SUBMITTED) is True

    def test_submitted_is_terminal(self) -> None:
        assert ReviewStatus.SUBMITTED.can_transition_to(ReviewStatus.DRAFT) is False

    def test_same_status_transition_is_rejected(self) -> None:
        assert ReviewStatus.DRAFT.can_transition_to(ReviewStatus.DRAFT) is False
