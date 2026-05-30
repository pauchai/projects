from community.domain.community import Community
from community.domain.ports import CommunityUnitOfWork


class CreateCommunityUseCase:
    def __init__(self, uow: CommunityUnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        community_id: str,
        name: str,
        description: str,
        owner_id: str,
        avatar_url: str | None = None,
    ) -> Community:
        with self._uow as uow:
            community = Community(
                community_id=community_id,
                name=name,
                description=description,
                owner_id=owner_id,
                avatar_url=avatar_url,
            )
            uow.communities.save(community)
            uow.commit()
            return community
