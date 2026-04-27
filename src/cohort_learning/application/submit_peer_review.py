"""SubmitPeerReview use case."""

from cohort_learning.application._helpers import (
    get_cohort_or_raise,
    require_cohort_member,
)
from cohort_learning.domain.peer_review import PeerReview
from cohort_learning.domain.ports import UnitOfWork
from cohort_learning.domain.review_score import ReviewScore


class SubmitPeerReviewUseCase:
    """A cohort member submits a review of another member's task submission.

    The reviewer must be an active cohort member and must not be the
    submission author. The review is created and immediately submitted
    (Draft -> Submitted) with the provided scores and feedback.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        review_id: str,
        submission_id: str,
        task_id: str,
        reviewer_id: str,
        scores: list[ReviewScore],
        overall_feedback: str = "",
    ) -> PeerReview:
        with self._uow as uow:
            task = uow.practice_tasks.find_by_id(task_id)
            if task is None:
                raise LookupError(f"Task {task_id} not found")

            submission = task.find_submission(submission_id)
            if submission is None:
                raise LookupError(f"Submission {submission_id} not found")

            cohort = get_cohort_or_raise(uow, task.cohort_id)
            require_cohort_member(cohort, reviewer_id)

            if reviewer_id == submission.learner_id:
                raise PermissionError("A reviewer cannot review their own submission")

            review = PeerReview(
                review_id=review_id,
                submission_id=submission_id,
                reviewer_id=reviewer_id,
                task_id=task_id,
                cohort_id=task.cohort_id,
            )
            review.submit(scores=scores, overall_feedback=overall_feedback)

            uow.peer_reviews.save(review)
            uow.commit()
            return review
