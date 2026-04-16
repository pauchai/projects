"""Use case: Create a new ModuleProgression."""

from cohort_learning.domain.module_progression import ModuleProgression
from cohort_learning.domain.ports import UnitOfWork


class CreateModuleUseCase:
    """Any authenticated user can create a module; becomes its master."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, module_id: str, title: str, caller_id: str) -> ModuleProgression:
        """Create and persist a new ModuleProgression.

        Args:
            module_id: Caller-supplied unique identifier.
            title: Human-readable module name (must not be empty).
            caller_id: ID of the authenticated user; becomes master_id.

        Returns:
            The newly created ModuleProgression.

        Raises:
            ValueError: If the title is empty or a module with this ID already exists.
        """
        with self._uow as uow:
            existing = uow.modules.find_by_id(module_id)
            if existing is not None:
                raise ValueError(f"Module '{module_id}' already exists")
            module = ModuleProgression(
                module_id=module_id,
                title=title,
                master_id=caller_id,
            )
            uow.modules.save(module)
            uow.commit()
            return module
