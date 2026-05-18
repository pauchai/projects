"""Platform Settings API router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from auth.api.dependencies import get_current_user_id
from guarantorship.api.dependencies import get_guarantorship_uow
from guarantorship.api.schemas import PlatformSettingsResponse, PlatformSettingsUpdate
from guarantorship.application.platform_settings import (
    GetPlatformSettingsUseCase,
    UpdatePlatformSettingsCommand,
    UpdatePlatformSettingsUseCase,
)
from guarantorship.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyGuarantorshipUnitOfWork

router = APIRouter(prefix="/platform-settings", tags=["platform-settings"])


@router.get("", response_model=PlatformSettingsResponse)
def get_platform_settings(
    uow: SqlAlchemyGuarantorshipUnitOfWork = Depends(get_guarantorship_uow),
) -> PlatformSettingsResponse:
    use_case = GetPlatformSettingsUseCase(uow)
    settings = use_case.execute()
    return PlatformSettingsResponse.model_validate(settings)


@router.patch("", response_model=PlatformSettingsResponse)
def update_platform_settings(
    body: PlatformSettingsUpdate,
    _user_id: str = Depends(get_current_user_id),  # TODO: admin check
    uow: SqlAlchemyGuarantorshipUnitOfWork = Depends(get_guarantorship_uow),
) -> PlatformSettingsResponse:
    use_case = UpdatePlatformSettingsUseCase(uow)
    try:
        settings = use_case.execute(
            UpdatePlatformSettingsCommand(
                required_guarantors_count=body.required_guarantors_count,
                guarantor_ward_limit=body.guarantor_ward_limit,
                escalation_levels=body.escalation_levels,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return PlatformSettingsResponse.model_validate(settings)
