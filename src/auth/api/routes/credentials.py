"""Credentials routes: view connected authentication methods."""

from fastapi import APIRouter, Depends

from auth.api.dependencies import get_auth_uow, get_current_user_id
from auth.api.schemas import CredentialSchema, CredentialsListResponse
from auth.application.view_user_credentials import ViewUserCredentialsUseCase
from auth.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/auth", tags=["credentials"])


@router.get("/credentials", response_model=CredentialsListResponse)
def get_user_credentials(
    caller_id: str = Depends(get_current_user_id),
    uow: SqlAlchemyUnitOfWork = Depends(get_auth_uow),
) -> CredentialsListResponse:
    """Return all credentials (sign-in methods) for the authenticated user."""
    use_case = ViewUserCredentialsUseCase(uow)
    result = use_case.execute(caller_id)

    return CredentialsListResponse(
        user_email=result.user_email,
        user_display_name=result.user_display_name,
        credentials=[
            CredentialSchema(
                credential_id=c.credential_id,
                provider=c.provider,
                provider_display_name=c.provider_display_name,
                provider_user_id=c.provider_user_id,
                is_removable=c.is_removable,
            )
            for c in result.credentials
        ],
        total_count=result.total_count,
        has_local_credential=result.has_local_credential,
    )
