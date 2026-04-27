"""CohortMembership entity — relationship between a learner and a cohort."""

from datetime import datetime, timezone

from cohort_learning.domain.cohort_role import CohortRole


class CohortMembership:
    """A learner's participation in a cohort with a progressive role."""

    def __init__(
        self,
        membership_id: str,
        learner_id: str,
        cohort_id: str,
    ) -> None:
        self.membership_id = membership_id
        self.learner_id = learner_id
        self.cohort_id = cohort_id
        self.role: CohortRole = CohortRole.LEARNER
        self.is_active: bool = True
        self.joined_at: datetime = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """Mark membership as inactive. Raises if already inactive."""
        if not self.is_active:
            raise ValueError("Membership is already inactive")
        self.is_active = False

    def promote_to(self, new_role: CohortRole) -> None:
        """Promote the member to a higher role. Cannot demote or assign Master."""
        if not self.is_active:
            raise ValueError("Cannot promote on inactive membership")
        if new_role == CohortRole.MASTER:
            raise ValueError("Cannot promote to Master via membership promotion")
        if new_role.rank <= self.role.rank:
            raise ValueError(
                f"Cannot demote from {self.role.value} to {new_role.value}"
            )
        self.role = new_role
