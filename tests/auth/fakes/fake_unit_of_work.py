"""Fake in-memory implementations of auth ports for testing."""

import copy

from auth.domain.user import User, Credential


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

    def save(self, user: User) -> None:
        self._storage[user.user_id] = user

    def snapshot(self) -> dict[str, User]:
        """Return a deep copy of the storage for rollback support."""
        return copy.deepcopy(self._storage)

    def restore(self, snapshot: dict[str, User]) -> None:
        """Restore storage from a snapshot."""
        self._storage = snapshot


class FakeUnitOfWork:
    """Fake UoW for auth testing: in-memory with commit/rollback semantics."""

    def __init__(self) -> None:
        self.users = FakeUserRepository()
        self.committed = False
        self._snapshot: dict[str, User] | None = None

    def __enter__(self) -> "FakeUnitOfWork":
        self.committed = False
        self._snapshot = self.users.snapshot()
        return self

    def __exit__(self, *args: object) -> None:
        if not self.committed:
            self.rollback()
        self._snapshot = None

    def commit(self) -> None:
        self.committed = True
        self._snapshot = None

    def rollback(self) -> None:
        if self._snapshot is not None:
            self.users.restore(self._snapshot)
            self._snapshot = None


class FakePasswordHasher:
    """Fake password hasher: uses a predictable prefix for testing."""

    def hash(self, plain_password: str) -> str:
        return f"hashed:{plain_password}"

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return hashed_password == f"hashed:{plain_password}"


class FakeTokenService:
    """Fake token service: returns a predictable token for testing."""

    def create_access_token(self, user_id: str) -> str:
        return f"fake-token:{user_id}"

    def decode_token(self, token: str) -> str:
        """Decode a fake token. Raises ValueError if format is invalid."""
        prefix = "fake-token:"
        if not token.startswith(prefix):
            raise ValueError("Invalid token")
        return token[len(prefix) :]
