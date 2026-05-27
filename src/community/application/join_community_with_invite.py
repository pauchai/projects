from __future__ import annotations

import uuid

from community.domain.community_role import CommunityRole
from community.domain.ports import CommunityUnitOfWork


class JoinCommunityWithInviteUseCase:
    def __init__(self, uow: CommunityUnitOfWork) -> None:
        self._uow = uow

    def execute(self, user_id: str, invite_code: str) -> str:
        with self._uow as uow:
            normalized_code = invite_code.strip().upper()
            code_entity = uow.invite_codes.find_by_code(normalized_code)
            if code_entity is None or not code_entity.is_valid():
                raise ValueError("Invite code is invalid or has expired")

            community = uow.communities.find_by_id(code_entity.community_id)
            if community is None:
                raise LookupError("Community not found")

            already_member = any(
                m.user_id == user_id and m.is_active
                for m in community.memberships
            )
            if already_member:
                raise ValueError("You are already an active member of this community")

            try:
                role = CommunityRole(code_entity.role)
            except ValueError:
                role = CommunityRole.MEMBER

            membership = community.add_member(
                membership_id=str(uuid.uuid4()),
                user_id=user_id,
                role=role,
            )

            code_entity.redeem()

            uow.invite_codes.save(code_entity)
            uow.communities.save(community)
            uow.commit()

            return membership.membership_id
