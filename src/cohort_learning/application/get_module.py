"""Use case: Get a single ModuleProgression by ID."""

from cohort_learning.domain.module_progression import ModuleProgression
from cohort_learning.domain.ports import UnitOfWork


class GetModuleUseCase:
    """Fetch a single module with its topics."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, module_id: str) -> ModuleProgression:
        """Return the ModuleProgression for the given ID.

        Args:
            module_id: Target module identifier.

        Returns:
            The ModuleProgression with topics loaded.

        Raises:
            LookupError: If the module does not exist.
        """
        with self._uow as uow:
            module = uow.modules.find_by_id(module_id)
            if module is None:
                raise LookupError(f"Module '{module_id}' not found")
            return module
