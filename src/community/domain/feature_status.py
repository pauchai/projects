from enum import Enum


class FeatureStatus(Enum):
    SUBMITTED = "submitted"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    REJECTED = "rejected"

    def can_transition_to(self, target: "FeatureStatus") -> bool:
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
}
