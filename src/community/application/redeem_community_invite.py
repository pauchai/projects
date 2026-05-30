from __future__ import annotations

import uuid

from community.domain.community_role import CommunityRole
from community.domain.ports import CommunityUnitOfWork


class RedeemCommunityInviteUseCase:
    """Add a newly registered user to a community as a member.

    Called immediately after successful registration when the invite code
    had ``scope="community"``.
    """

    def __init__(self, uow: CommunityUnitOfWork) -> None:
        self._uow = uow

    def execute(self, user_id: str, community_id: str, role_value: str) -> str:
        with self._uow as uow:
            community = uow.communities.find_by_id(community_id)
            if community is None:
                raise LookupError(f"Community '{community_id}' not found")

            already_member = any(
                m.user_id == user_id and m.is_active
                for m in community.memberships
            )
            if already_member:
                raise ValueError(
                    f"User '{user_id}' is already an active member of community '{community_id}'"
                )

            try:
                role = CommunityRole(role_value)
            except ValueError:
                role = CommunityRole.MEMBER

            membership = community.add_member(
                membership_id=str(uuid.uuid4()),
                user_id=user_id,
                role=role,
            )
            uow.communities.save(community)
            uow.commit()
            return membership.membership_id
