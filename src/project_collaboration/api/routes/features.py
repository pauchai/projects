"""Feature request routes: REST endpoints for the Feature Request API."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from project_collaboration.api.dependencies import get_current_user_id, get_uow
from project_collaboration.api.schemas import (
    CreateFeatureRequestRequest,
    FeatureRequestResponse,
    MessageResponse,
    UpdateFeatureStatusRequest,
)
from project_collaboration.application.list_feature_requests import (
    ListFeatureRequestsUseCase,
)
from project_collaboration.application.submit_feature_request import (
    SubmitFeatureRequestUseCase,
)
from project_collaboration.application.update_feature_status import (
    UpdateFeatureStatusUseCase,
)
from project_collaboration.domain.feature_request import FeatureRequest
from project_collaboration.domain.feature_status import FeatureStatus
from project_collaboration.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)

router = APIRouter(tags=["features"])


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def _feature_request_to_response(fr: FeatureRequest) -> FeatureRequestResponse:
    return FeatureRequestResponse(
        request_id=fr.request_id,
        author_id=fr.author_id,
        title=fr.title,
        description=fr.description,
        status=fr.status.value,
        category=fr.category,
        priority=fr.priority,
        admin_notes=fr.admin_notes,
        created_at=fr.created_at,
        updated_at=fr.updated_at,
    )


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


@router.get("/features", response_model=list[FeatureRequestResponse])
def list_features(
    status: str | None = None,
    author_id: str | None = None,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> list[FeatureRequestResponse]:
    """List all feature requests with optional filters."""
    use_case = ListFeatureRequestsUseCase(uow)

    parsed_status: FeatureStatus | None = None
    if status is not None:
        parsed_status = FeatureStatus(status)

    results = use_case.execute(status=parsed_status, author_id=author_id)
    return [_feature_request_to_response(fr) for fr in results]


@router.post("/features", status_code=201, response_model=FeatureRequestResponse)
def create_feature_request(
    body: CreateFeatureRequestRequest,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> FeatureRequestResponse:
    """Submit a new feature request. Requires authentication."""
    use_case = SubmitFeatureRequestUseCase(uow)
    result = use_case.execute(
        request_id=body.request_id,
        author_id=caller_id,
        title=body.title,
        description=body.description,
        category=body.category,
        priority=body.priority,
    )
    return _feature_request_to_response(result)


@router.get("/features/{request_id}", response_model=FeatureRequestResponse)
def get_feature_request(
    request_id: str,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> FeatureRequestResponse:
    """Get a feature request by ID."""
    with uow:
        fr = uow.feature_requests.find_by_id(request_id)
        if fr is None:
            raise LookupError(f"Feature request {request_id} not found")
        return _feature_request_to_response(fr)


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


@router.put(
    "/admin/features/{request_id}/status",
    response_model=MessageResponse,
)
def update_feature_status(
    request_id: str,
    body: UpdateFeatureStatusRequest,
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> MessageResponse:
    """Update the status of a feature request (admin only).

    NOTE: Admin authorization is not enforced yet — any authenticated user
    can call this endpoint. Admin checks will be added when the admin role
    system is implemented.
    """
    use_case = UpdateFeatureStatusUseCase(uow)
    new_status = FeatureStatus(body.status)
    use_case.execute(
        request_id=request_id,
        new_status=new_status,
        admin_notes=body.admin_notes,
    )
    return MessageResponse(
        message=f"Feature request status updated to {new_status.value}"
    )
