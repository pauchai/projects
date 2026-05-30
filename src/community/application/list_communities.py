from community.domain.community import Community
from community.domain.community_status import CommunityStatus
from community.domain.ports import CommunityUnitOfWork


class ListCommunitiesUseCase:
    def __init__(self, uow: CommunityUnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        caller_id: str,
        owner_id: str | None = None,
        status: CommunityStatus | None = None,
        keyword: str | None = None,
    ) -> list[Community]:
        with self._uow as uow:
            return uow.communities.search(
                owner_id=owner_id,
                member_user_id=caller_id if owner_id is None else None,
                status=status,
                keyword=keyword,
            )


class GetCommunityUseCase:
    def __init__(self, uow: CommunityUnitOfWork) -> None:
        self._uow = uow

    def execute(self, community_id: str, caller_id: str) -> Community:
        with self._uow as uow:
            community = uow.communities.find_by_id(community_id)
            if community is None:
                raise LookupError(f"Community {community_id} not found")
            return community
