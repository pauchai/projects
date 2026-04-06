"""AuthenticateWithOAuth use case — exchanges an OAuth code for a JWT token.

Handles three scenarios:
1. New user → creates User + OAuth Credential → returns token.
2. Existing user without this provider's credential → links credential → returns token.
3. Existing user already has the credential → returns token (login).
"""

import uuid

from auth.domain.oauth import OAuthUserInfo
from auth.domain.ports import OAuthClient, TokenService, UnitOfWork
from auth.domain.user import Credential, User


class AuthenticateWithOAuthUseCase:
    """Authenticates (or registers) a user via an OAuth provider.

    Delegates the OAuth protocol to the injected ``OAuthClient`` port.
    The use case owns the business rules: account merging, credential linking,
    and user creation.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        oauth_client: OAuthClient,
        token_service: TokenService,
    ) -> None:
        self._uow = uow
        self._oauth_client = oauth_client
        self._token_service = token_service

    def execute(self, code: str) -> str:
        """Exchange an authorization code for a JWT access token.

        Raises:
            OAuthError: if the OAuth provider rejects the code or user info request.
            ValueError: if the matched user account is inactive.
        """
        access_token = self._oauth_client.exchange_code(code)
        user_info = self._oauth_client.get_user_info(access_token)

        with self._uow as uow:
            user = uow.users.find_by_email(user_info.email)

            if user is None:
                user = self._create_new_user(user_info)
            else:
                if not user.is_active:
                    raise ValueError("User account is inactive")
                self._link_credential_if_needed(user, user_info)

            uow.users.save(user)
            uow.commit()

            return self._token_service.create_access_token(user.user_id)

    def _create_new_user(self, user_info: OAuthUserInfo) -> User:
        """Create a brand-new User with an OAuth credential."""
        user_id = str(uuid.uuid4())
        user = User(
            user_id=user_id,
            email=user_info.email,
            display_name=user_info.display_name,
        )
        credential = Credential(
            credential_id=str(uuid.uuid4()),
            user_id=user_id,
            provider=user_info.provider,
            provider_user_id=user_info.provider_user_id,
            hashed_secret=None,
        )
        user.add_credential(credential)
        return user

    def _link_credential_if_needed(self, user: User, user_info: OAuthUserInfo) -> None:
        """Link an OAuth credential to an existing user if not already present."""
        if not user.has_credential_for_provider(user_info.provider):
            credential = Credential(
                credential_id=str(uuid.uuid4()),
                user_id=user.user_id,
                provider=user_info.provider,
                provider_user_id=user_info.provider_user_id,
                hashed_secret=None,
            )
            user.add_credential(credential)
