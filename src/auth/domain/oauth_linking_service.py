"""Domain service for safely linking an OAuth credential to a user.

This service encapsulates the business rules for credential linking:
- The user must not already have a credential for the given provider.
- The OAuth account (provider_user_id) must not belong to another user.

The service is a pure domain concept — no infrastructure dependencies.
The caller (Application Service) is responsible for looking up the
existing owner and passing it in.
"""

import uuid

from auth.domain.oauth import OAuthAccountAlreadyLinkedError, OAuthUserInfo
from auth.domain.user import Credential, User


class OAuthCredentialLinkingService:
    """Links an OAuth credential to a user, enforcing business rules."""

    def link(
        self,
        user: User,
        oauth_info: OAuthUserInfo,
        existing_owner: User | None,
    ) -> None:
        """Link an OAuth credential to *user*.

        Args:
            user: The user who wants to add the OAuth provider.
            oauth_info: Profile data from the OAuth provider.
            existing_owner: The user who currently owns this OAuth account
                (looked up by the caller via ``provider_user_id``), or
                ``None`` if no one owns it yet.

        Raises:
            OAuthAccountAlreadyLinkedError: If the OAuth account is already
                linked to a *different* user.
            ValueError: If the user already has a credential for this provider.
        """
        # Rule 1: OAuth account must not belong to a different user.
        if existing_owner is not None and existing_owner.user_id != user.user_id:
            raise OAuthAccountAlreadyLinkedError(
                provider=oauth_info.provider,
                owner_user_id=existing_owner.user_id,
            )

        # Rule 2: User must not already have this provider.
        if user.has_credential_for_provider(oauth_info.provider):
            raise ValueError(f"User already has a credential for {oauth_info.provider}")

        # All checks passed — create and attach the credential.
        credential = Credential(
            credential_id=str(uuid.uuid4()),
            user_id=user.user_id,
            provider=oauth_info.provider,
            provider_user_id=oauth_info.provider_user_id,
            hashed_secret=None,
        )
        user.add_credential(credential)
