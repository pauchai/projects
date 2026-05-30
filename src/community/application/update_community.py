from community.application._helpers import get_community_or_raise, require_community_role
from community.domain.community_role import CommunityRole
from community.domain.ports import CommunityUnitOfWork


class UpdateCommunityUseCase:
    def __init__(self, uow: CommunityUnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        community_id: str,
        caller_id: str,
        name: str | None = None,
        description: str | None = None,
        avatar_url: str | None = None,
    ) -> None:
        with self._uow as uow:
            community = get_community_or_raise(uow, community_id)
            require_community_role(community, caller_id, CommunityRole.OWNER, CommunityRole.ADMIN)
            community.update_profile(
                name=name,
                description=description,
                avatar_url=avatar_url,
            )
            uow.communities.save(community)
            uow.commit()
