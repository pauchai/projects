"""PeerReview aggregate root — a cohort member's review of a task submission."""

from __future__ import annotations

from datetime import datetime, timezone

from cohort_learning.domain.events import PeerReviewSubmitted
from cohort_learning.domain.review_score import ReviewScore
from cohort_learning.domain.review_status import ReviewStatus
from shared_kernel.events import DomainEvent


class PeerReview:
    """Aggregate root for a peer review of a task submission.

    A cohort member evaluates another member's submission using
    criterion-based scoring and written feedback.

    Business rules:
    - A review must have at least one score to be submitted.
    - Duplicate criteria in a single review are not allowed.
    - Once submitted, a review cannot be modified.
    - Reviewer must not be the submission author (enforced by use case).
    """

    def __init__(
        self,
        review_id: str,
        submission_id: str,
        reviewer_id: str,
        task_id: str,
        cohort_id: str,
    ) -> None:
        self.review_id = review_id
        self.submission_id = submission_id
        self.reviewer_id = reviewer_id
        self.task_id = task_id
        self.cohort_id = cohort_id
        self.status: ReviewStatus = ReviewStatus.DRAFT
        self.scores: list[ReviewScore] = []
        self.overall_feedback: str = ""
        self.created_at: datetime = datetime.now(timezone.utc)
        self.reviewed_at: datetime | None = None

        self._events: list[DomainEvent] = []

    # -------------------------------------------------------------------------
    # Event helpers
    # -------------------------------------------------------------------------

    def collect_events(self) -> list[DomainEvent]:
        """Return and clear uncommitted domain events."""
        events = list(self._events)
        self._events.clear()
        return events

    def _emit(self, event: DomainEvent) -> None:
        self._events.append(event)

    # -------------------------------------------------------------------------
    # Submit review
    # -------------------------------------------------------------------------

    def submit(
        self,
        scores: list[ReviewScore],
        overall_feedback: str = "",
    ) -> None:
        """Submit the completed review with criterion scores and feedback.

        Raises ValueError if:
        - Review has already been submitted.
        - No scores provided.
        - Duplicate criteria in scores.
        """
        if self.status == ReviewStatus.SUBMITTED:
            raise ValueError("Review has already been submitted")

        if not scores:
            raise ValueError("Review must contain at least one criterion score")

        criteria = [s.criterion for s in scores]
        if len(criteria) != len(set(criteria)):
            raise ValueError("Duplicate criteria in review scores")

        self.scores = list(scores)
        self.overall_feedback = overall_feedback
        self.status = ReviewStatus.SUBMITTED
        self.reviewed_at = datetime.now(timezone.utc)

        self._emit(
            PeerReviewSubmitted(
                review_id=self.review_id,
                submission_id=self.submission_id,
                reviewer_id=self.reviewer_id,
                task_id=self.task_id,
                cohort_id=self.cohort_id,
            )
        )

    # -------------------------------------------------------------------------
    # Queries
    # -------------------------------------------------------------------------

    @property
    def average_score(self) -> float | None:
        """Return average score across all criteria, or None if not submitted."""
        if not self.scores:
            return None
        return sum(s.score for s in self.scores) / len(self.scores)
