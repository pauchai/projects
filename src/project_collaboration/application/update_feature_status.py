"""UpdateFeatureStatus use case."""

from project_collaboration.domain.feature_status import FeatureStatus
from project_collaboration.domain.ports import UnitOfWork


class UpdateFeatureStatusUseCase:
    """Transitions a feature request to a new status (admin operation)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        request_id: str,
        new_status: FeatureStatus,
        admin_notes: str | None = None,
    ) -> None:
        with self._uow as uow:
            feature_request = uow.feature_requests.find_by_id(request_id)
            if feature_request is None:
                raise LookupError(f"Feature request {request_id} not found")
            feature_request.change_status(new_status)
            if admin_notes is not None:
                feature_request.set_admin_notes(admin_notes)
            uow.feature_requests.save(feature_request)
            uow.commit()
