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
