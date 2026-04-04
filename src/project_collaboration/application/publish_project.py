"""PublishProject use case."""

from project_collaboration.domain.ports import UnitOfWork


class PublishProjectUseCase:
    """Transitions a project from Draft to Recruiting."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, project_id: str) -> None:
        with self._uow as uow:
            project = uow.projects.find_by_id(project_id)
            if project is None:
                raise LookupError(f"Project {project_id} not found")
            project.publish()
            uow.projects.save(project)
            uow.commit()
