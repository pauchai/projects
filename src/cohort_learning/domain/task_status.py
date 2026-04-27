"""Task and submission lifecycle statuses with allowed transitions."""

from enum import Enum


class TaskStatus(Enum):
    """Lifecycle phase of a practice task."""

    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"

    def can_transition_to(self, target: "TaskStatus") -> bool:
        """Check if transition from self to target is allowed."""
        if self == target:
            return False
        return target in _TASK_TRANSITIONS.get(self, set())


_TASK_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.DRAFT: {TaskStatus.ACTIVE, TaskStatus.CLOSED},
    TaskStatus.ACTIVE: {TaskStatus.CLOSED},
    # CLOSED is terminal — no transitions out
}


class SubmissionStatus(Enum):
    """Lifecycle phase of a task submission."""

    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REVISION_REQUESTED = "revision_requested"

    def can_transition_to(self, target: "SubmissionStatus") -> bool:
        """Check if transition from self to target is allowed."""
        if self == target:
            return False
        return target in _SUBMISSION_TRANSITIONS.get(self, set())


_SUBMISSION_TRANSITIONS: dict[SubmissionStatus, set[SubmissionStatus]] = {
    SubmissionStatus.SUBMITTED: {SubmissionStatus.IN_REVIEW},
    SubmissionStatus.IN_REVIEW: {
        SubmissionStatus.APPROVED,
        SubmissionStatus.REVISION_REQUESTED,
    },
    SubmissionStatus.REVISION_REQUESTED: {SubmissionStatus.SUBMITTED},
    # APPROVED is terminal — no transitions out
}
