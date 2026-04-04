"""PublishProject use case."""

from project_collaboration.application._helpers import get_project_or_raise
from project_collaboration.domain.ports import UnitOfWork


class PublishProjectUseCase:
    """Transitions a project from Draft to Recruiting."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, project_id: str, caller_id: str) -> None:
        with self._uow as uow:
            project = get_project_or_raise(uow, project_id)
            if not project.is_owner(caller_id):
                raise PermissionError("Only the project owner can publish the project")
            project.publish()
            uow.projects.save(project)
            uow.commit()
