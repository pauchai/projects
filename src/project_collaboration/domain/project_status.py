"""Project lifecycle status with allowed transitions."""

from enum import Enum


class ProjectStatus(Enum):
    """Lifecycle phase of a project."""

    DRAFT = "draft"
    RECRUITING = "recruiting"
    ACTIVE = "active"
    COMPLETED = "completed"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

    def can_transition_to(self, target: "ProjectStatus") -> bool:
        """Check if transition from self to target is allowed."""
        if self == target:
            return False
        return target in _ALLOWED_TRANSITIONS.get(self, set())


_ALLOWED_TRANSITIONS: dict[ProjectStatus, set[ProjectStatus]] = {
    ProjectStatus.DRAFT: {ProjectStatus.RECRUITING},
    ProjectStatus.RECRUITING: {
        ProjectStatus.ACTIVE,
        ProjectStatus.SUSPENDED,
        ProjectStatus.CANCELLED,
    },
    ProjectStatus.ACTIVE: {
        ProjectStatus.COMPLETED,
        ProjectStatus.SUSPENDED,
        ProjectStatus.CANCELLED,
    },
    ProjectStatus.SUSPENDED: {
        ProjectStatus.ACTIVE,
        ProjectStatus.RECRUITING,
    },
    # COMPLETED and CANCELLED are terminal — no transitions out
}
