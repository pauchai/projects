"""LearningCohort aggregate root — a group of learners studying a module together."""

from __future__ import annotations

from datetime import datetime, timezone

from cohort_learning.domain.cohort_membership import CohortMembership
from cohort_learning.domain.cohort_status import CohortStatus
from cohort_learning.domain.events import (
    CohortActivated,
    CohortCancelled,
    CohortFormed,
    CohortGraduated,
    LearnerEnrolled,
    LearnerRemoved,
)
from shared_kernel.events import DomainEvent

MIN_LEARNERS = 3
MAX_LEARNERS = 15


class LearningCohort:
    """Aggregate root for a learning cohort.

    A time-bounded group of learners who study a single module
    together under the guidance of a master.

    V1 constraints:
    - 5–15 learners per cohort
    - 1 master per cohort
    - Enrollment only during Forming status
    """

    def __init__(
        self,
        cohort_id: str,
        master_id: str,
        module_id: str,
    ) -> None:
        self.cohort_id = cohort_id
        self.master_id = master_id
        self.module_id = module_id
        self.status = CohortStatus.FORMING
        self.formed_at: datetime = datetime.now(timezone.utc)

        self.memberships: list[CohortMembership] = []
        self._events: list[DomainEvent] = []

        self._emit(
            CohortFormed(
                cohort_id=cohort_id,
                master_id=master_id,
                module_id=module_id,
            )
        )

    # -------------------------------------------------------------------------
    # Event helpers
    # -------------------------------------------------------------------------

    def collect_events(self) -> list[DomainEvent]:
        """Return and clear uncommitted domain events."""
        events = list(self._events)
        self._events.clear()
        return events

    def _emit(self, event: DomainEvent) -> None:
        self._events.append(event)

    # -------------------------------------------------------------------------
    # Enrollment
    # -------------------------------------------------------------------------

    def enrol_learner(self, membership_id: str, learner_id: str) -> None:
        """Enrol a learner into this cohort.

        Raises ValueError if:
        - Cohort is not in Forming status
        - Learner is already enrolled
        - Learner is the master
        - Maximum learner count reached
        """
        if self.status != CohortStatus.FORMING:
            raise ValueError("Enrollment is only allowed when cohort is Forming")

        if learner_id == self.master_id:
            raise ValueError("Master cannot enrol as a learner in their own cohort")

        if any(m.learner_id == learner_id and m.is_active for m in self.memberships):
            raise ValueError(
                f"Learner '{learner_id}' is already enrolled in this cohort"
            )

        if self.active_learner_count >= MAX_LEARNERS:
            raise ValueError(
                f"Cohort has reached the maximum of {MAX_LEARNERS} learners"
            )

        membership = CohortMembership(
            membership_id=membership_id,
            learner_id=learner_id,
            cohort_id=self.cohort_id,
        )
        self.memberships.append(membership)

        self._emit(
            LearnerEnrolled(
                cohort_id=self.cohort_id,
                membership_id=membership_id,
                learner_id=learner_id,
            )
        )

    # -------------------------------------------------------------------------
    # Learner removal
    # -------------------------------------------------------------------------

    def remove_learner(self, membership_id: str) -> None:
        """Remove a learner by deactivating their membership."""
        membership = self._find_membership(membership_id)
        membership.deactivate()
        self._emit(
            LearnerRemoved(
                cohort_id=self.cohort_id,
                membership_id=membership_id,
                learner_id=membership.learner_id,
            )
        )

    # -------------------------------------------------------------------------
    # Status transitions
    # -------------------------------------------------------------------------

    def _transition_to(self, target: CohortStatus) -> None:
        if not self.status.can_transition_to(target):
            raise ValueError(
                f"Cannot transition from {self.status.value} to {target.value}"
            )
        self.status = target

    def activate(self) -> None:
        """Forming -> Active. Requires minimum learner count."""
        if not self.status.can_transition_to(CohortStatus.ACTIVE):
            raise ValueError(
                f"Cannot transition from {self.status.value} to {CohortStatus.ACTIVE.value}"
            )
        if self.active_learner_count < MIN_LEARNERS:
            raise ValueError(
                f"Cannot activate cohort: minimum {MIN_LEARNERS} learners required, "
                f"but only {self.active_learner_count} enrolled"
            )
        self.status = CohortStatus.ACTIVE
        self._emit(CohortActivated(cohort_id=self.cohort_id))

    def begin_completing(self) -> None:
        """Active -> Completing."""
        self._transition_to(CohortStatus.COMPLETING)

    def graduate(self) -> None:
        """Completing -> Graduated (terminal)."""
        self._transition_to(CohortStatus.GRADUATED)
        self._emit(CohortGraduated(cohort_id=self.cohort_id))

    def cancel(self) -> None:
        """Forming/Active/Completing -> Cancelled (terminal)."""
        self._transition_to(CohortStatus.CANCELLED)
        self._emit(CohortCancelled(cohort_id=self.cohort_id))

    # -------------------------------------------------------------------------
    # Queries
    # -------------------------------------------------------------------------

    @property
    def active_learner_count(self) -> int:
        """Return the number of currently active learners."""
        return sum(1 for m in self.memberships if m.is_active)

    def find_membership_by_learner_id(self, learner_id: str) -> CohortMembership | None:
        """Return the active membership for a learner, or None."""
        for m in self.memberships:
            if m.learner_id == learner_id and m.is_active:
                return m
        return None

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _find_membership(self, membership_id: str) -> CohortMembership:
        for m in self.memberships:
            if m.membership_id == membership_id:
                return m
        raise LookupError(f"Membership '{membership_id}' not found")
