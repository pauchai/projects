"""ManageMember use cases: change role and remove member."""

from project_collaboration.application._helpers import (
    get_project_or_raise,
    require_management_rights,
)
from project_collaboration.domain.ports import UnitOfWork
from project_collaboration.domain.role import ProjectRole


class ChangeMemberRoleUseCase:
    """Changes a member's role within a project."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        project_id: str,
        membership_id: str,
        new_role: ProjectRole,
        caller_id: str,
    ) -> None:
        with self._uow as uow:
            project = get_project_or_raise(uow, project_id)
            require_management_rights(project, caller_id)
            project.change_member_role(membership_id=membership_id, new_role=new_role)
            uow.projects.save(project)
            uow.commit()


class RemoveMemberUseCase:
    """Removes a member from a project by deactivating their membership."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, project_id: str, membership_id: str, caller_id: str) -> None:
        with self._uow as uow:
            project = get_project_or_raise(uow, project_id)
            require_management_rights(project, caller_id)
            project.remove_member(membership_id=membership_id)
            uow.projects.save(project)
            uow.commit()
