"""OAuth value objects and exceptions for the Auth domain.

These are pure domain concepts — no infrastructure dependencies.
``OAuthUserInfo`` represents the user profile data obtained from an
OAuth provider after a successful authentication flow.
``OAuthError`` is raised when the OAuth flow fails at any stage.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OAuthUserInfo:
    """User profile data returned by an OAuth provider.

    This is a Value Object — immutable and compared by value.
    The domain uses it to decide whether to create a new user
    or link a credential to an existing one.
    """

    provider: str
    provider_user_id: str
    email: str
    display_name: str


class OAuthError(Exception):
    """Raised when an OAuth operation fails.

    Covers: invalid authorization code, network errors communicating
    with the provider, missing/invalid user info, etc.
    """


class OAuthAccountAlreadyLinkedError(Exception):
    """Raised when an OAuth account is already linked to a different user.

    This happens when a user tries to link a Google/Telegram account
    that is already associated with another user in the system.
    """

    def __init__(self, provider: str, owner_user_id: str) -> None:
        self.provider = provider
        self.owner_user_id = owner_user_id
        super().__init__(
            f"This {provider} account is already connected to another user"
        )
