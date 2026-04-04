"""ReviewApplication use cases: accept and reject."""

from abc import ABC, abstractmethod

from project_collaboration.application._helpers import (
    get_project_or_raise,
    require_management_rights,
)
from project_collaboration.domain.ports import UnitOfWork
from project_collaboration.domain.project import Project


class _ReviewApplicationUseCase(ABC):
    """Base class for accepting/rejecting applications.

    Subclasses implement ``_review`` to perform the domain action.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, project_id: str, application_id: str, caller_id: str) -> None:
        with self._uow as uow:
            project = get_project_or_raise(uow, project_id)
            require_management_rights(project, caller_id)
            self._review(project, application_id, caller_id)
            uow.projects.save(project)
            uow.commit()

    @abstractmethod
    def _review(
        self, project: Project, application_id: str, caller_id: str
    ) -> None: ...


class AcceptApplicationUseCase(_ReviewApplicationUseCase):
    """Accepts a pending application, creating a new membership."""

    def _review(self, project: Project, application_id: str, caller_id: str) -> None:
        project.accept_application(application_id=application_id, reviewed_by=caller_id)


class RejectApplicationUseCase(_ReviewApplicationUseCase):
    """Rejects a pending application."""

    def _review(self, project: Project, application_id: str, caller_id: str) -> None:
        project.reject_application(application_id=application_id, reviewed_by=caller_id)
