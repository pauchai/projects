import uuid

from community.application._helpers import get_community_or_raise, require_community_role
from community.domain.community_membership import CommunityMembership
from community.domain.community_role import CommunityRole
from community.domain.ports import CommunityUnitOfWork


class AddMemberUseCase:
    def __init__(self, uow: CommunityUnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        community_id: str,
        caller_id: str,
        user_id: str,
        role: CommunityRole = CommunityRole.MEMBER,
    ) -> CommunityMembership:
        with self._uow as uow:
            community = get_community_or_raise(uow, community_id)
            require_community_role(community, caller_id, CommunityRole.OWNER, CommunityRole.ADMIN)

            membership = community.add_member(
                membership_id=str(uuid.uuid4()),
                user_id=user_id,
                role=role,
            )
            uow.communities.save(community)
            uow.commit()
            return membership


class RemoveMemberUseCase:
    def __init__(self, uow: CommunityUnitOfWork) -> None:
        self._uow = uow

    def execute(self, community_id: str, caller_id: str, user_id: str) -> None:
        with self._uow as uow:
            community = get_community_or_raise(uow, community_id)
            require_community_role(community, caller_id, CommunityRole.OWNER, CommunityRole.ADMIN)
            community.remove_member(user_id)
            uow.communities.save(community)
            uow.commit()


class ChangeMemberRoleUseCase:
    def __init__(self, uow: CommunityUnitOfWork) -> None:
        self._uow = uow

    def execute(
        self, community_id: str, caller_id: str, user_id: str, new_role: CommunityRole
    ) -> None:
        with self._uow as uow:
            community = get_community_or_raise(uow, community_id)
            require_community_role(community, caller_id, CommunityRole.OWNER, CommunityRole.ADMIN)
            community.change_member_role(user_id, new_role)
            uow.communities.save(community)
            uow.commit()
