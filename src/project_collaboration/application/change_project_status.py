"""ChangeProjectStatus use cases: activate, suspend, resume, complete, cancel."""

from project_collaboration.domain.ports import UnitOfWork


class _BaseStatusUseCase:
    """Shared logic: find project within UoW, delegate to method, save, commit."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def _find_project(self, uow, project_id: str):
        project = uow.projects.find_by_id(project_id)
        if project is None:
            raise LookupError(f"Project {project_id} not found")
        return project

    def _find_project_as_owner(self, uow, project_id: str, caller_id: str):
        project = self._find_project(uow, project_id)
        if not project.is_owner(caller_id):
            raise PermissionError("Only the project owner can change project status")
        return project


class ActivateProjectUseCase(_BaseStatusUseCase):
    """Transitions a project from Recruiting to Active."""

    def execute(self, project_id: str, caller_id: str) -> None:
        with self._uow as uow:
            project = self._find_project_as_owner(uow, project_id, caller_id)
            project.activate()
            uow.projects.save(project)
            uow.commit()


class SuspendProjectUseCase(_BaseStatusUseCase):
    """Transitions a project to Suspended, remembering previous status."""

    def execute(self, project_id: str, caller_id: str) -> None:
        with self._uow as uow:
            project = self._find_project_as_owner(uow, project_id, caller_id)
            project.suspend()
            uow.projects.save(project)
            uow.commit()


class ResumeProjectUseCase(_BaseStatusUseCase):
    """Resumes a suspended project to its previous status."""

    def execute(self, project_id: str, caller_id: str) -> None:
        with self._uow as uow:
            project = self._find_project_as_owner(uow, project_id, caller_id)
            project.resume()
            uow.projects.save(project)
            uow.commit()


class CompleteProjectUseCase(_BaseStatusUseCase):
    """Transitions a project from Active to Completed (terminal)."""

    def execute(self, project_id: str, caller_id: str) -> None:
        with self._uow as uow:
            project = self._find_project_as_owner(uow, project_id, caller_id)
            project.complete()
            uow.projects.save(project)
            uow.commit()


class CancelProjectUseCase(_BaseStatusUseCase):
    """Transitions a project to Cancelled (terminal)."""

    def execute(self, project_id: str, caller_id: str) -> None:
        with self._uow as uow:
            project = self._find_project_as_owner(uow, project_id, caller_id)
            project.cancel()
            uow.projects.save(project)
            uow.commit()
