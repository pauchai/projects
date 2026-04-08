"""Feature request lifecycle status with allowed transitions."""

from enum import Enum


class FeatureStatus(Enum):
    """Lifecycle phase of a feature request."""

    SUBMITTED = "submitted"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    REJECTED = "rejected"

    def can_transition_to(self, target: "FeatureStatus") -> bool:
        """Check if transition from self to target is allowed."""
        if self == target:
            return False
        return target in _ALLOWED_TRANSITIONS.get(self, set())


_ALLOWED_TRANSITIONS: dict[FeatureStatus, set[FeatureStatus]] = {
    FeatureStatus.SUBMITTED: {FeatureStatus.PLANNED, FeatureStatus.REJECTED},
    FeatureStatus.PLANNED: {FeatureStatus.IN_PROGRESS, FeatureStatus.REJECTED},
    FeatureStatus.IN_PROGRESS: {
        FeatureStatus.DONE,
        FeatureStatus.REJECTED,
        FeatureStatus.PLANNED,
    },
    # DONE and REJECTED are terminal — no transitions out
}
