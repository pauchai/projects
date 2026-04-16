"""ChangeCohortStatus use cases: activate, begin_completing, graduate, cancel."""

from abc import ABC, abstractmethod

from cohort_learning.application._helpers import get_cohort_or_raise, require_master
from cohort_learning.domain.learning_cohort import LearningCohort
from cohort_learning.domain.ports import UnitOfWork


class _BaseStatusUseCase(ABC):
    """Template method: find cohort as master, change status, save, commit.

    Subclasses implement ``_change_status`` to perform the domain action.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, cohort_id: str, caller_id: str) -> None:
        with self._uow as uow:
            cohort = get_cohort_or_raise(uow, cohort_id)
            require_master(cohort, caller_id)
            self._change_status(cohort)
            uow.cohorts.save(cohort)
            uow.commit()

    @abstractmethod
    def _change_status(self, cohort: LearningCohort) -> None: ...


class ActivateCohortUseCase(_BaseStatusUseCase):
    """Transitions a cohort from Forming to Active."""

    def _change_status(self, cohort: LearningCohort) -> None:
        cohort.activate()


class BeginCompletingCohortUseCase(_BaseStatusUseCase):
    """Transitions a cohort from Active to Completing."""

    def _change_status(self, cohort: LearningCohort) -> None:
        cohort.begin_completing()


class GraduateCohortUseCase(_BaseStatusUseCase):
    """Transitions a cohort from Completing to Graduated (terminal)."""

    def _change_status(self, cohort: LearningCohort) -> None:
        cohort.graduate()


class CancelCohortUseCase(_BaseStatusUseCase):
    """Transitions a cohort to Cancelled (terminal)."""

    def _change_status(self, cohort: LearningCohort) -> None:
        cohort.cancel()
