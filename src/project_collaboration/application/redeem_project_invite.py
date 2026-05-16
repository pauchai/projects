"""RedeemProjectInviteUseCase — create a Membership from a project-scoped invite.

This use case is called by the auth API handler *after* RegisterUserWithInviteUseCase
has already validated, redeemed and committed the invite code.  It lives in
project_collaboration and knows nothing about InviteCode — it only receives the
resolved project_id and role as plain strings (SRP: each context owns its part).

Raises:
    LookupError: if the project does not exist.
    ValueError: if the user is already an active member of the project.
"""

from __future__ import annotations

import uuid

from project_collaboration.domain.membership import Membership
from project_collaboration.domain.ports import UnitOfWork
from project_collaboration.domain.role import ProjectRole


class RedeemProjectInviteUseCase:
    """Add a newly registered user to a project as a member.

    Called immediately after successful registration when the invite code
    had ``scope="project"``.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, user_id: str, project_id: str, role_value: str) -> str:
        """Create a Membership and return the membership_id.

        Args:
            user_id:    The newly registered user's ID.
            project_id: The project they should join.
            role_value: The role string from the invite code (e.g. "member").
        """
        with self._uow as uow:
            project = uow.projects.find_by_id(project_id)
            if project is None:
                raise LookupError(f"Project '{project_id}' not found")

            # Guard: do not create duplicate active memberships
            already_member = any(
                m.user_id == user_id and m.is_active
                for m in project.memberships
            )
            if already_member:
                raise ValueError(
                    f"User '{user_id}' is already an active member of project '{project_id}'"
                )

            try:
                role = ProjectRole(role_value)
            except ValueError:
                role = ProjectRole.MEMBER  # safe fallback

            membership = Membership(
                membership_id=str(uuid.uuid4()),
                user_id=user_id,
                project_id=project_id,
                role=role,
            )
            project.memberships.append(membership)
            uow.projects.save(project)
            uow.commit()
            return membership.membership_id
