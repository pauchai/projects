"""ListFeatureRequests use case: read-only query for feature requests."""

from project_collaboration.domain.feature_request import FeatureRequest
from project_collaboration.domain.feature_status import FeatureStatus
from project_collaboration.domain.ports import UnitOfWork


class ListFeatureRequestsUseCase:
    """Returns feature requests matching optional filters.

    Read-only query — no domain events, no state changes.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        status: FeatureStatus | None = None,
        author_id: str | None = None,
    ) -> list[FeatureRequest]:
        with self._uow as uow:
            return uow.feature_requests.find_all(
                status=status,
                author_id=author_id,
            )
