"""ReviewApplication use cases: accept and reject."""

from project_collaboration.domain.ports import UnitOfWork


class AcceptApplicationUseCase:
    """Accepts a pending application, creating a new membership."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, project_id: str, application_id: str, reviewed_by: str) -> None:
        with self._uow as uow:
            project = uow.projects.find_by_id(project_id)
            if project is None:
                raise LookupError(f"Project {project_id} not found")
            if not project.has_management_rights(reviewed_by):
                raise PermissionError(
                    "Reviewer lacks management rights to review applications"
                )
            project.accept_application(
                application_id=application_id, reviewed_by=reviewed_by
            )
            uow.projects.save(project)
            uow.commit()


class RejectApplicationUseCase:
    """Rejects a pending application."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, project_id: str, application_id: str, reviewed_by: str) -> None:
        with self._uow as uow:
            project = uow.projects.find_by_id(project_id)
            if project is None:
                raise LookupError(f"Project {project_id} not found")
            if not project.has_management_rights(reviewed_by):
                raise PermissionError(
                    "Reviewer lacks management rights to review applications"
                )
            project.reject_application(
                application_id=application_id, reviewed_by=reviewed_by
            )
            uow.projects.save(project)
            uow.commit()
