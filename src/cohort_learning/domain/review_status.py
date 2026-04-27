"""Peer review lifecycle status with allowed transitions."""

from enum import Enum


class ReviewStatus(Enum):
    """Lifecycle phase of a peer review."""

    DRAFT = "draft"
    SUBMITTED = "submitted"

    def can_transition_to(self, target: "ReviewStatus") -> bool:
        """Check if transition from self to target is allowed."""
        if self == target:
            return False
        return target in _REVIEW_TRANSITIONS.get(self, set())


_REVIEW_TRANSITIONS: dict[ReviewStatus, set[ReviewStatus]] = {
    ReviewStatus.DRAFT: {ReviewStatus.SUBMITTED},
    # SUBMITTED is terminal — no transitions out
}
