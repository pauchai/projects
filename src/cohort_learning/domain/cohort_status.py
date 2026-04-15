"""Cohort lifecycle status with allowed transitions."""

from enum import Enum


class CohortStatus(Enum):
    """Lifecycle phase of a learning cohort."""

    FORMING = "forming"
    ACTIVE = "active"
    COMPLETING = "completing"
    GRADUATED = "graduated"
    CANCELLED = "cancelled"

    def can_transition_to(self, target: "CohortStatus") -> bool:
        """Check if transition from self to target is allowed."""
        if self == target:
            return False
        return target in _ALLOWED_TRANSITIONS.get(self, set())


_ALLOWED_TRANSITIONS: dict[CohortStatus, set[CohortStatus]] = {
    CohortStatus.FORMING: {CohortStatus.ACTIVE, CohortStatus.CANCELLED},
    CohortStatus.ACTIVE: {CohortStatus.COMPLETING, CohortStatus.CANCELLED},
    CohortStatus.COMPLETING: {CohortStatus.GRADUATED, CohortStatus.CANCELLED},
    # GRADUATED and CANCELLED are terminal — no transitions out
}
