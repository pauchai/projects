"""Use case: List all modules (public catalog)."""

from cohort_learning.domain.module_progression import ModuleProgression
from cohort_learning.domain.ports import UnitOfWork


class ListModulesUseCase:
    """Return all ModuleProgressions in the system (public catalog)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self) -> list[ModuleProgression]:
        """Return all modules with their topics.

        Returns:
            List of all ModuleProgressions, unfiltered.
        """
        with self._uow as uow:
            return uow.modules.find_all()
