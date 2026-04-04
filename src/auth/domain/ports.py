"""Driven ports (Protocols) for the Auth bounded context.

These interfaces are defined by the domain layer and implemented by infrastructure.
Domain never depends on infrastructure — only on these abstractions (DIP).
"""

from typing import Protocol

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


class UserRepository(Protocol):
    """Port for persisting and querying Users in the Auth context."""

    def find_by_id(self, user_id: str) -> User | None: ...

    def find_by_email(self, email: str) -> User | None: ...

    def save(self, user: User) -> None: ...


class UnitOfWork(Protocol):
    """Driven port: coordinates atomic persistence for the Auth context.

    Application Services manage the UoW lifecycle (enter, commit/rollback, exit).
    The domain layer defines this contract; infrastructure provides the real
    implementation. Tests use a FakeUnitOfWork.

    Usage::

        with uow:
            user = uow.users.find_by_email("alice@example.com")
            user.add_credential(credential)
            uow.users.save(user)
            uow.commit()
    """

    users: UserRepository

    def __enter__(self) -> "UnitOfWork": ...
    def __exit__(self, *args: object) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
