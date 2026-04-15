"""Tests for PeerReview aggregate root."""

import pytest

from cohort_learning.domain.events import PeerReviewSubmitted
from cohort_learning.domain.peer_review import PeerReview
from cohort_learning.domain.review_score import ReviewScore
from cohort_learning.domain.review_status import ReviewStatus


class TestPeerReviewCreation:
    """PeerReview is an aggregate root recording a cohort member's review."""

    def test_stores_review_id(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        assert review.review_id == "rev1"

    def test_stores_submission_id(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        assert review.submission_id == "sub1"

    def test_stores_reviewer_id(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        assert review.reviewer_id == "learner2"

    def test_stores_task_id(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        assert review.task_id == "task1"

    def test_stores_cohort_id(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        assert review.cohort_id == "c1"

    def test_default_status_is_draft(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        assert review.status == ReviewStatus.DRAFT

    def test_scores_initially_empty(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        assert review.scores == []

    def test_overall_feedback_defaults_to_empty(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        assert review.overall_feedback == ""

    def test_created_at_is_set(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        assert review.created_at is not None

    def test_reviewed_at_is_none_initially(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        assert review.reviewed_at is None


class TestPeerReviewSubmit:
    """Submitting a review transitions Draft -> Submitted with scores and feedback."""

    def test_submit_transitions_to_submitted(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        scores = [
            ReviewScore(criterion="clarity", score=4),
            ReviewScore(criterion="correctness", score=5),
        ]
        review.submit(scores=scores, overall_feedback="Good work!")
        assert review.status == ReviewStatus.SUBMITTED

    def test_submit_stores_scores(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        scores = [
            ReviewScore(criterion="clarity", score=4),
            ReviewScore(criterion="correctness", score=5),
        ]
        review.submit(scores=scores, overall_feedback="Good work!")
        assert len(review.scores) == 2
        assert review.scores[0].criterion == "clarity"
        assert review.scores[1].criterion == "correctness"

    def test_submit_stores_overall_feedback(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        scores = [ReviewScore(criterion="clarity", score=4)]
        review.submit(scores=scores, overall_feedback="Well done!")
        assert review.overall_feedback == "Well done!"

    def test_submit_sets_reviewed_at(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        scores = [ReviewScore(criterion="clarity", score=4)]
        review.submit(scores=scores, overall_feedback="Good")
        assert review.reviewed_at is not None

    def test_submit_emits_peer_review_submitted_event(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        scores = [ReviewScore(criterion="clarity", score=4)]
        review.submit(scores=scores, overall_feedback="Good")
        events = review.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], PeerReviewSubmitted)
        assert events[0].review_id == "rev1"
        assert events[0].submission_id == "sub1"
        assert events[0].reviewer_id == "learner2"
        assert events[0].task_id == "task1"
        assert events[0].cohort_id == "c1"


class TestPeerReviewValidation:
    """PeerReview enforces business rules on submission."""

    def test_submit_raises_when_already_submitted(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        scores = [ReviewScore(criterion="clarity", score=4)]
        review.submit(scores=scores, overall_feedback="Good")
        with pytest.raises(ValueError, match="already.*submitted"):
            review.submit(scores=scores, overall_feedback="Again")

    def test_submit_raises_with_empty_scores(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        with pytest.raises(ValueError, match="at least one"):
            review.submit(scores=[], overall_feedback="Good")

    def test_submit_raises_with_duplicate_criteria(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        scores = [
            ReviewScore(criterion="clarity", score=4),
            ReviewScore(criterion="clarity", score=5),
        ]
        with pytest.raises(ValueError, match="[Dd]uplicate"):
            review.submit(scores=scores, overall_feedback="Good")


class TestPeerReviewQueries:
    """PeerReview provides computed properties."""

    def test_average_score(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        scores = [
            ReviewScore(criterion="clarity", score=4),
            ReviewScore(criterion="correctness", score=2),
        ]
        review.submit(scores=scores, overall_feedback="Good")
        assert review.average_score == 3.0

    def test_average_score_returns_none_when_draft(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        assert review.average_score is None


class TestPeerReviewCollectEvents:
    """PeerReview collects and clears events like other aggregates."""

    def test_collect_events_returns_and_clears(self) -> None:
        review = PeerReview(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner2",
            task_id="task1",
            cohort_id="c1",
        )
        scores = [ReviewScore(criterion="clarity", score=4)]
        review.submit(scores=scores, overall_feedback="Good")
        events = review.collect_events()
        assert len(events) == 1
        # Second call returns empty
        assert review.collect_events() == []
