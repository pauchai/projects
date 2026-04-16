"""TaskSubmission entity — a learner's solution for a practice task."""

from datetime import datetime, timezone

from cohort_learning.domain.task_status import SubmissionStatus


class TaskSubmission:
    """A learner's submitted solution for a practice task.

    Follows a review workflow:
    Submitted → In Review → Approved | Revision Requested → Submitted (resubmit).
    """

    def __init__(
        self,
        submission_id: str,
        task_id: str,
        learner_id: str,
        content: str,
    ) -> None:
        if not content.strip():
            raise ValueError("Submission content must not be empty")

        self.submission_id = submission_id
        self.task_id = task_id
        self.learner_id = learner_id
        self.content = content
        self.status: SubmissionStatus = SubmissionStatus.SUBMITTED
        self.submitted_at: datetime = datetime.now(timezone.utc)

    # -------------------------------------------------------------------------
    # Status transitions
    # -------------------------------------------------------------------------

    def _transition_to(self, target: SubmissionStatus) -> None:
        if not self.status.can_transition_to(target):
            raise ValueError(
                f"Cannot transition from {self.status.value} to {target.value}"
            )
        self.status = target

    def begin_review(self) -> None:
        """Submitted → In Review."""
        self._transition_to(SubmissionStatus.IN_REVIEW)

    def approve(self) -> None:
        """In Review → Approved."""
        self._transition_to(SubmissionStatus.APPROVED)

    def request_revision(self) -> None:
        """In Review → Revision Requested."""
        self._transition_to(SubmissionStatus.REVISION_REQUESTED)

    def resubmit(self, new_content: str) -> None:
        """Revision Requested → Submitted with updated content."""
        if not new_content.strip():
            raise ValueError("Submission content must not be empty")
        self._transition_to(SubmissionStatus.SUBMITTED)
        self.content = new_content
        self.submitted_at = datetime.now(timezone.utc)
