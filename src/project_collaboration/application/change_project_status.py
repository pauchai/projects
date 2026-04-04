"""ChangeProjectStatus use cases: activate, suspend, resume, complete, cancel."""

from abc import ABC, abstractmethod

from project_collaboration.application._helpers import get_project_or_raise
from project_collaboration.domain.ports import UnitOfWork
from project_collaboration.domain.project import Project


class _BaseStatusUseCase(ABC):
    """Template method: find project as owner, change status, save, commit.

    Subclasses implement ``_change_status`` to perform the domain action.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, project_id: str, caller_id: str) -> None:
        with self._uow as uow:
            project = get_project_or_raise(uow, project_id)
            if not project.is_owner(caller_id):
                raise PermissionError(
                    "Only the project owner can change project status"
                )
            self._change_status(project)
            uow.projects.save(project)
            uow.commit()

    @abstractmethod
    def _change_status(self, project: Project) -> None: ...


class ActivateProjectUseCase(_BaseStatusUseCase):
    """Transitions a project from Recruiting to Active."""

    def _change_status(self, project: Project) -> None:
        project.activate()


class SuspendProjectUseCase(_BaseStatusUseCase):
    """Transitions a project to Suspended, remembering previous status."""

    def _change_status(self, project: Project) -> None:
        project.suspend()


class ResumeProjectUseCase(_BaseStatusUseCase):
    """Resumes a suspended project to its previous status."""

    def _change_status(self, project: Project) -> None:
        project.resume()


class CompleteProjectUseCase(_BaseStatusUseCase):
    """Transitions a project from Active to Completed (terminal)."""

    def _change_status(self, project: Project) -> None:
        project.complete()


class CancelProjectUseCase(_BaseStatusUseCase):
    """Transitions a project to Cancelled (terminal)."""

    def _change_status(self, project: Project) -> None:
        project.cancel()
