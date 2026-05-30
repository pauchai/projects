from community.application._helpers import get_community_or_raise, require_community_role
from community.domain.community_role import CommunityRole
from community.domain.feature_request import FeatureRequest
from community.domain.feature_status import FeatureStatus
from community.domain.ports import CommunityUnitOfWork


class SubmitFeatureRequestUseCase:
    def __init__(self, uow: CommunityUnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        request_id: str,
        community_id: str,
        author_id: str,
        title: str,
        description: str,
        category: str | None = None,
        priority: str | None = None,
    ) -> FeatureRequest:
        with self._uow as uow:
            community = get_community_or_raise(uow, community_id)
            require_community_role(community, author_id, CommunityRole.MEMBER)

            feature_request = FeatureRequest(
                request_id=request_id,
                community_id=community_id,
                author_id=author_id,
                title=title,
                description=description,
                category=category,
                priority=priority,
            )
            uow.feature_requests.save(feature_request)
            uow.commit()
            return feature_request


class ListFeatureRequestsUseCase:
    def __init__(self, uow: CommunityUnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        community_id: str,
        caller_id: str,
        status: FeatureStatus | None = None,
        author_id: str | None = None,
    ) -> list[FeatureRequest]:
        with self._uow as uow:
            community = get_community_or_raise(uow, community_id)
            require_community_role(community, caller_id, CommunityRole.MEMBER)
            return uow.feature_requests.find_all(
                community_id=community_id,
                status=status,
                author_id=author_id,
            )


class UpdateFeatureStatusUseCase:
    def __init__(self, uow: CommunityUnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        request_id: str,
        caller_id: str,
        new_status: FeatureStatus,
        admin_notes: str | None = None,
    ) -> None:
        with self._uow as uow:
            feature_request = uow.feature_requests.find_by_id(request_id)
            if feature_request is None:
                raise LookupError(f"Feature request {request_id} not found")

            community = get_community_or_raise(uow, feature_request.community_id)
            require_community_role(community, caller_id, CommunityRole.OWNER, CommunityRole.ADMIN)

            feature_request.change_status(new_status)
            if admin_notes is not None:
                feature_request.set_admin_notes(admin_notes)
            uow.feature_requests.save(feature_request)
            uow.commit()
