"""Use case: Add a Topic to a ModuleProgression."""

from cohort_learning.domain.module_progression import ModuleProgression
from cohort_learning.domain.ports import UnitOfWork
from cohort_learning.domain.topic import Topic


class AddTopicToModuleUseCase:
    """Add a topic to an existing module."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        module_id: str,
        topic_id: str,
        title: str,
        position: int,
        description: str = "",
    ) -> ModuleProgression:
        """Append a new topic to the module's ordered sequence.

        Args:
            module_id: Target module identifier.
            topic_id: Caller-supplied unique topic identifier.
            title: Topic title (must not be empty).
            position: Non-negative integer ordering position (must be unique).
            description: Optional topic description.

        Returns:
            The updated ModuleProgression.

        Raises:
            LookupError: If the module does not exist.
            ValueError: If title is empty, position is negative, or position/id clash.
        """
        with self._uow as uow:
            module = uow.modules.find_by_id(module_id)
            if module is None:
                raise LookupError(f"Module '{module_id}' not found")
            topic = Topic(
                topic_id=topic_id,
                title=title,
                position=position,
                description=description,
            )
            module.add_topic(topic)
            uow.modules.save(module)
            uow.commit()
            return module
