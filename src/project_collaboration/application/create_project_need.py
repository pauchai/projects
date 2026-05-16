"""CreateProjectNeedUseCase — any active project member can post a need."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from project_collaboration.domain.ports import UnitOfWork
from project_collaboration.domain.project_need import ProjectNeed
from project_collaboration.domain.role import ProjectRole


@dataclass(frozen=True)
class CreateProjectNeedCommand:
    project_id: str
    caller_id: str          # user_id of the member creating the need
    role: ProjectRole
    description: str
    skills: list[str]
    slots: int = 1


class CreateProjectNeedUseCase:
    """Let any active project member publish an open position.

    Raises:
        LookupError: if the project does not exist.
        PermissionError: if the caller is not an active member of the project.
        ValueError: from ProjectNeed domain validation (empty description, etc.).
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, cmd: CreateProjectNeedCommand) -> str:
        with self._uow as uow:
            project = uow.projects.find_by_id(cmd.project_id)
            if project is None:
                raise LookupError(f"Project '{cmd.project_id}' not found")

            # Verify caller is an active member
            is_member = any(
                m.user_id == cmd.caller_id and m.is_active
                for m in project.memberships
            )
            if not is_member:
                raise PermissionError(
                    "Only active project members can create a project need"
                )

            need = ProjectNeed(
                need_id=str(uuid.uuid4()),
                project_id=cmd.project_id,
                role=cmd.role,
                description=cmd.description,
                created_by=cmd.caller_id,
                skills=cmd.skills,
                slots=cmd.slots,
            )
            uow.needs.save(need)
            uow.commit()
            return need.need_id
