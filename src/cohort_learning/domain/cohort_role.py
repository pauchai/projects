"""Cohort role with privilege hierarchy and progression order."""

from enum import Enum


class CohortRole(Enum):
    """Role of a participant within a learning cohort, ordered by progression."""

    LEARNER = "learner"
    TOPIC_EXPERT = "topic_expert"
    MODULE_CURATOR = "module_curator"
    MASTER = "master"

    def can_review_tasks(self) -> bool:
        """Return True if this role can review practice tasks."""
        return self in {
            CohortRole.TOPIC_EXPERT,
            CohortRole.MODULE_CURATOR,
            CohortRole.MASTER,
        }

    def can_curate(self) -> bool:
        """Return True if this role can curate cohorts."""
        return self in {CohortRole.MODULE_CURATOR, CohortRole.MASTER}

    @property
    def rank(self) -> int:
        """Numeric rank for progression comparison."""
        return _ROLE_RANKS[self]


_ROLE_RANKS: dict["CohortRole", int] = {
    CohortRole.LEARNER: 0,
    CohortRole.TOPIC_EXPERT: 1,
    CohortRole.MODULE_CURATOR: 2,
    CohortRole.MASTER: 3,
}
