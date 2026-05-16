"""CloseProjectNeedUseCase — close an open project need."""

from __future__ import annotations

from project_collaboration.domain.ports import UnitOfWork


class CloseProjectNeedUseCase:
    """Close an open project need.

    Any active member of the project can close any need (not only the creator).

    Raises:
        LookupError: if the need does not exist.
        PermissionError: if the caller is not an active member of the project.
        ValueError: if the need is already closed (raised by domain).
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, need_id: str, caller_id: str) -> None:
        with self._uow as uow:
            need = uow.needs.find_by_id(need_id)
            if need is None:
                raise LookupError(f"ProjectNeed '{need_id}' not found")

            project = uow.projects.find_by_id(need.project_id)
            if project is None:
                raise LookupError(f"Project '{need.project_id}' not found")

            is_member = any(
                m.user_id == caller_id and m.is_active
                for m in project.memberships
            )
            if not is_member:
                raise PermissionError(
                    "Only active project members can close a project need"
                )

            need.close()
            uow.needs.save(need)
            uow.commit()
