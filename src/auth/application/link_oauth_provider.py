"""LinkOAuthProvider use case — links an OAuth credential to an authenticated user.

Called from the settings page when a user wants to add a new sign-in method
(e.g., connect their Google or Telegram account).

The use case:
1. Exchanges the authorization code for user info via OAuthClient.
2. Checks that the OAuth account isn't already owned by another user.
3. Delegates the business rules to OAuthCredentialLinkingService.
4. Persists the change atomically via UoW.
"""

from auth.domain.oauth_linking_service import OAuthCredentialLinkingService
from auth.domain.ports import OAuthClient, UnitOfWork


class LinkOAuthProviderUseCase:
    """Links an OAuth provider to an existing, authenticated user.

    Raises:
        LookupError: If the user does not exist.
        ValueError: If the user is inactive or already has this provider.
        OAuthError: If the OAuth provider rejects the code or user info request.
        OAuthAccountAlreadyLinkedError: If the OAuth account belongs to another user.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        oauth_client: OAuthClient,
    ) -> None:
        self._uow = uow
        self._oauth_client = oauth_client
        self._linking_service = OAuthCredentialLinkingService()

    def execute(self, user_id: str, code: str) -> None:
        """Exchange *code* for OAuth profile and link it to *user_id*."""
        access_token = self._oauth_client.exchange_code(code)
        oauth_info = self._oauth_client.get_user_info(access_token)

        with self._uow as uow:
            user = uow.users.find_by_id(user_id)
            if user is None:
                raise LookupError(f"User {user_id} not found")
            if not user.is_active:
                raise ValueError("User account is inactive")

            # Check if another user already owns this OAuth account.
            existing_owner = uow.users.find_by_oauth_provider_user_id(
                provider=oauth_info.provider,
                provider_user_id=oauth_info.provider_user_id,
            )

            # Delegate business rules to the domain service.
            self._linking_service.link(
                user=user,
                oauth_info=oauth_info,
                existing_owner=existing_owner,
            )

            uow.users.save(user)
            uow.commit()
