"""View user credentials use case — returns credential summaries for the UI."""

from __future__ import annotations

from dataclasses import dataclass

from auth.domain.ports import UnitOfWork
from auth.domain.user import CredentialSummary


@dataclass(frozen=True)
class ViewUserCredentialsResult:
    """Immutable result returned to the API layer."""

    user_email: str
    user_display_name: str
    credentials: list[CredentialSummary]
    total_count: int
    has_local_credential: bool


class ViewUserCredentialsUseCase:
    """Return all credential summaries for the authenticated user.

    Raises:
        LookupError: If the user does not exist.
        ValueError: If the user account is inactive.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, user_id: str) -> ViewUserCredentialsResult:
        with self._uow as uow:
            user = uow.users.find_by_id(user_id)
            if user is None:
                raise LookupError(f"User {user_id} not found")
            if not user.is_active:
                raise ValueError("User account is inactive")

            credentials = user.list_credential_summaries()

            return ViewUserCredentialsResult(
                user_email=user.email,
                user_display_name=user.display_name,
                credentials=credentials,
                total_count=len(credentials),
                has_local_credential=user.has_credential_for_provider("local"),
            )
