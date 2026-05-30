from community.application._helpers import get_community_or_raise, require_community_role
from community.domain.community_role import CommunityRole
from community.domain.community_status import CommunityStatus
from community.domain.ports import CommunityUnitOfWork


class ChangeCommunityStatusUseCase:
    def __init__(self, uow: CommunityUnitOfWork) -> None:
        self._uow = uow

    def execute(
        self, community_id: str, caller_id: str, target_status: CommunityStatus
    ) -> None:
        with self._uow as uow:
            community = get_community_or_raise(uow, community_id)
            require_community_role(community, caller_id, CommunityRole.OWNER)

            if target_status == CommunityStatus.SUSPENDED:
                community.suspend()
            elif target_status == CommunityStatus.ARCHIVED:
                community.archive()
            elif target_status == CommunityStatus.ACTIVE:
                community.reactivate()
            else:
                raise ValueError(f"Unsupported target status: {target_status}")

            uow.communities.save(community)
            uow.commit()
