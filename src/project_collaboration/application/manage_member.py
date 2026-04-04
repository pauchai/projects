"""ManageMember use cases: change role and remove member."""

from project_collaboration.domain.ports import UnitOfWork
from project_collaboration.domain.role import ProjectRole


class ChangeMemberRoleUseCase:
    """Changes a member's role within a project."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self, project_id: str, membership_id: str, new_role: ProjectRole
    ) -> None:
        with self._uow as uow:
            project = uow.projects.find_by_id(project_id)
            if project is None:
                raise LookupError(f"Project {project_id} not found")
            project.change_member_role(membership_id=membership_id, new_role=new_role)
            uow.projects.save(project)
            uow.commit()


class RemoveMemberUseCase:
    """Removes a member from a project by deactivating their membership."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, project_id: str, membership_id: str) -> None:
        with self._uow as uow:
            project = uow.projects.find_by_id(project_id)
            if project is None:
                raise LookupError(f"Project {project_id} not found")
            project.remove_member(membership_id=membership_id)
            uow.projects.save(project)
            uow.commit()
