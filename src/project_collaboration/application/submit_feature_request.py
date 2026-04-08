"""SubmitFeatureRequest use case."""

from project_collaboration.domain.feature_request import FeatureRequest
from project_collaboration.domain.ports import UnitOfWork


class SubmitFeatureRequestUseCase:
    """Creates a new feature request in Submitted status."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        request_id: str,
        author_id: str,
        title: str,
        description: str,
        category: str | None = None,
        priority: str | None = None,
    ) -> FeatureRequest:
        with self._uow as uow:
            feature_request = FeatureRequest(
                request_id=request_id,
                author_id=author_id,
                title=title,
                description=description,
                category=category,
                priority=priority,
            )
            uow.feature_requests.save(feature_request)
            uow.commit()
            return feature_request
