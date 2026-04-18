"""Driven ports (Protocols) for the Auth bounded context.

These interfaces are defined by the domain layer and implemented by infrastructure.
Domain never depends on infrastructure — only on these abstractions (DIP).
"""

from typing import Protocol

from auth.domain.invite_code import InviteCode
from auth.domain.oauth import OAuthUserInfo
from auth.domain.telegram_auth_request import TelegramAuthRequest
from auth.domain.user import User


class PasswordHasher(Protocol):
    """Port for password hashing and verification."""

    def hash(self, plain_password: str) -> str: ...

    def verify(self, plain_password: str, hashed_password: str) -> bool: ...


class TokenService(Protocol):
    """Port for creating and decoding authentication tokens (e.g., JWT)."""

    def create_access_token(self, user_id: str) -> str: ...

    def decode_token(self, token: str) -> str:
        """Decode a token and return the user_id. Raises ValueError if invalid."""
        ...


class OAuthClient(Protocol):
    """Port for communicating with an OAuth provider.

    The domain defines *what* data it needs; infrastructure implements
    *how* to get it from a specific provider (Google, GitHub, etc.).

    The flow:
    1. ``build_authorization_url`` — generate the URL to redirect the user to.
    2. ``exchange_code`` — exchange the authorization code for an access token.
    3. ``get_user_info`` — fetch user profile data using the access token.
    """

    def build_authorization_url(self, state: str) -> str:
        """Return the provider's authorization URL with the given state parameter."""
        ...

    def exchange_code(self, code: str) -> str:
        """Exchange an authorization code for an access token.

        Raises ``OAuthError`` on failure (network, invalid code, etc.).
        """
        ...

    def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """Fetch user profile from the provider using the access token.

        Raises ``OAuthError`` on failure.
        """
        ...


class UserRepository(Protocol):
    """Port for persisting and querying Users in the Auth context."""

    def find_by_id(self, user_id: str) -> User | None: ...

    def find_by_email(self, email: str) -> User | None: ...

    def find_by_oauth_provider_user_id(
        self, provider: str, provider_user_id: str
    ) -> User | None:
        """Find a user who has a credential for the given provider + external ID."""
        ...

    def save(self, user: User) -> None: ...


class InviteCodeRepository(Protocol):
    """Port for persisting and querying InviteCodes."""

    def find_by_code(self, code: str) -> InviteCode | None: ...

    def save(self, invite_code: InviteCode) -> None: ...

    def save_all(self, invite_codes: list[InviteCode]) -> None: ...


class TelegramAuthRequestRepository(Protocol):
    """Port for persisting and querying TelegramAuthRequests.

    This repository is intentionally **not** part of the UnitOfWork.
    TelegramAuthRequests are short-lived coordination records stored in
    Redis with automatic TTL expiration — they do not participate in
    the same transaction as User/Credential persistence.
    """

    def find_by_auth_code(self, auth_code: str) -> TelegramAuthRequest | None: ...

    def find_by_authorization_code(
        self, authorization_code: str
    ) -> TelegramAuthRequest | None: ...

    def save(self, request: TelegramAuthRequest) -> None: ...

    def delete(self, auth_code: str) -> None:
        """Remove a TelegramAuthRequest by auth_code."""
        ...


class UnitOfWork(Protocol):
    """Driven port: coordinates atomic persistence for the Auth context.

    Application Services manage the UoW lifecycle (enter, commit/rollback, exit).
    The domain layer defines this contract; infrastructure provides the real
    implementation. Tests use a FakeUnitOfWork.

    Note: TelegramAuthRequestRepository is NOT part of the UoW — it uses
    Redis with TTL and does not participate in SQL transactions.

    Usage::

        with uow:
            user = uow.users.find_by_email("alice@example.com")
            user.add_credential(credential)
            uow.users.save(user)
            uow.commit()
    """

    users: UserRepository
    invite_codes: InviteCodeRepository

    def __enter__(self) -> "UnitOfWork": ...
    def __exit__(self, *args: object) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
