"""Shared helper functions for cohort_learning application-layer use cases."""

from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.domain.ports import UnitOfWork


def get_cohort_or_raise(uow: UnitOfWork, cohort_id: str) -> LearningCohort:
    """Fetch a cohort by ID or raise LookupError."""
    cohort = uow.cohorts.find_by_id(cohort_id)
    if cohort is None:
        raise LookupError(f"Cohort {cohort_id} not found")
    return cohort


def require_master(cohort: LearningCohort, caller_id: str) -> None:
    """Raise PermissionError if caller is not the cohort master."""
    if cohort.master_id != caller_id:
        raise PermissionError("Only the cohort master can perform this operation")


def require_master_or_curator(cohort: LearningCohort, caller_id: str) -> None:
    """Raise PermissionError if caller is not the master or a module curator.

    Allows the cohort master or any active member with a role that satisfies
    ``can_curate()`` (i.e. MODULE_CURATOR or MASTER role on membership).
    """
    if cohort.master_id == caller_id:
        return

    membership = cohort.find_membership_by_learner_id(caller_id)
    if membership is not None and membership.role.can_curate():
        return

    raise PermissionError(
        "Only the cohort master or module curator can perform this operation"
    )


def require_cohort_member(cohort: LearningCohort, learner_id: str) -> None:
    """Raise PermissionError if learner is not an active cohort member."""
    membership = cohort.find_membership_by_learner_id(learner_id)
    if membership is None:
        raise PermissionError(
            f"Learner '{learner_id}' is not an active member of this cohort"
        )
