"""Fake in-memory implementations of auth ports for testing."""

import copy

from auth.domain.oauth import OAuthError, OAuthUserInfo
from auth.domain.telegram_auth_request import TelegramAuthRequest
from auth.domain.user import User, Credential
from shared_kernel.events import DomainEvent, EventBus


class FakeUserRepository:
    """In-memory UserRepository used within FakeUnitOfWork."""

    def __init__(self) -> None:
        self._storage: dict[str, User] = {}

    def find_by_id(self, user_id: str) -> User | None:
        return self._storage.get(user_id)

    def find_by_email(self, email: str) -> User | None:
        normalized = email.strip().lower()
        for user in self._storage.values():
            if user.email == normalized:
                return user
        return None

    def find_by_oauth_provider_user_id(
        self, provider: str, provider_user_id: str
    ) -> User | None:
        """Find a user who has a credential matching provider + provider_user_id."""
        for user in self._storage.values():
            for cred in user.credentials:
                if (
                    cred.provider == provider
                    and cred.provider_user_id == provider_user_id
                ):
                    return user
        return None

    def find_by_inviter_id(self, inviter_id: str) -> list[User]:
        """Return all users who were invited by the given user_id."""
        return [u for u in self._storage.values() if u.inviter_id == inviter_id]

    def save(self, user: User) -> None:
        self._storage[user.user_id] = user

    def snapshot(self) -> dict[str, User]:
        """Return a deep copy of the storage for rollback support."""
        return copy.deepcopy(self._storage)

    def restore(self, snapshot: dict[str, User]) -> None:
        """Restore storage from a snapshot."""
        self._storage = snapshot


class FakeTelegramAuthRequestRepository:
    """In-memory TelegramAuthRequestRepository for testing.

    Standalone fake — not part of FakeUnitOfWork. TelegramAuthRequests
    are stored in Redis (not PostgreSQL) and do not participate in
    SQL transactions.
    """

    def __init__(self) -> None:
        self._storage: dict[str, TelegramAuthRequest] = {}

    def find_by_auth_code(self, auth_code: str) -> TelegramAuthRequest | None:
        return self._storage.get(auth_code)

    def find_by_authorization_code(
        self, authorization_code: str
    ) -> TelegramAuthRequest | None:
        for req in self._storage.values():
            if req.authorization_code == authorization_code:
                return req
        return None

    def save(self, request: TelegramAuthRequest) -> None:
        self._storage[request.auth_code] = request

    def delete(self, auth_code: str) -> None:
        self._storage.pop(auth_code, None)


class FakeUnitOfWork:
    """Fake UoW for auth testing: in-memory with commit/rollback semantics.

    Note: TelegramAuthRequestRepository is NOT part of the UoW — it uses
    Redis and is injected as a standalone dependency. Use
    ``FakeTelegramAuthRequestRepository`` separately in tests that need it.
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self.users = FakeUserRepository()
        self.committed = False
        self._user_snapshot: dict[str, User] | None = None
        self._event_bus = event_bus
        self._pending_events: list[DomainEvent] = []

    def __enter__(self) -> "FakeUnitOfWork":
        self.committed = False
        self._user_snapshot = self.users.snapshot()
        return self

    def __exit__(self, *args: object) -> None:
        if not self.committed:
            self.rollback()
        self._user_snapshot = None

    def commit(self) -> None:
        self.committed = True
        if self._event_bus and self._pending_events:
            self._event_bus.publish(self._pending_events)
        self._pending_events.clear()
        self._user_snapshot = None

    def rollback(self) -> None:
        if self._user_snapshot is not None:
            self.users.restore(self._user_snapshot)
            self._user_snapshot = None
        self._pending_events.clear()

    def collect_events(self, events: list[DomainEvent]) -> None:
        """Accumulate domain events for publishing after commit."""
        self._pending_events.extend(events)


class FakePasswordHasher:
    """Fake password hasher: uses a predictable prefix for testing."""

    def hash(self, plain_password: str) -> str:
        return f"hashed:{plain_password}"

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return hashed_password == f"hashed:{plain_password}"


class FakeTokenService:
    """Fake token service: returns a predictable token for testing."""

    def create_access_token(self, user_id: str, status: str = "active") -> str:
        return f"fake-token:{user_id}:{status}"

    def decode_token(self, token: str) -> str:
        """Decode a fake token. Raises ValueError if format is invalid."""
        prefix = "fake-token:"
        if not token.startswith(prefix):
            raise ValueError("Invalid token")
        # format: fake-token:<user_id>:<status>
        rest = token[len(prefix):]
        return rest.split(":")[0]

    def decode_token_full(self, token: str) -> dict:
        """Decode a fake token and return full payload dict."""
        prefix = "fake-token:"
        if not token.startswith(prefix):
            raise ValueError("Invalid token")
        rest = token[len(prefix):]
        parts = rest.split(":", 1)
        return {
            "user_id": parts[0],
            "status": parts[1] if len(parts) > 1 else "active",
        }


class FakeOAuthClient:
    """Fake OAuthClient for testing OAuth use cases.

    Configurable: set ``user_info`` to control what ``get_user_info`` returns,
    or set ``error`` to make ``exchange_code`` / ``get_user_info`` raise.
    """

    def __init__(
        self,
        user_info: OAuthUserInfo | None = None,
        error: OAuthError | None = None,
    ) -> None:
        self._user_info = user_info
        self._error = error
        self.exchanged_codes: list[str] = []

    def build_authorization_url(self, state: str) -> str:
        return f"https://fake-oauth.example.com/authorize?state={state}"

    def exchange_code(self, code: str) -> str:
        if self._error is not None:
            raise self._error
        self.exchanged_codes.append(code)
        return "fake-access-token"

    def get_user_info(self, access_token: str) -> OAuthUserInfo:
        if self._error is not None:
            raise self._error
        if self._user_info is None:
            raise OAuthError("No user info configured in FakeOAuthClient")
        return self._user_info
