"""Integration tests for SqlAlchemyUnitOfWork (auth context).

Tests verify that UoW commit/rollback semantics work correctly against PostgreSQL.
"""

import pytest
from sqlalchemy.orm import Session, sessionmaker

from auth.domain.user import Credential, User
from auth.infrastructure.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def _make_user(
    user_id: str = "user-1",
    email: str = "alice@example.com",
    display_name: str = "Alice",
) -> User:
    """Create a User with a local credential for testing."""
    user = User(user_id=user_id, email=email, display_name=display_name)
    credential = Credential(
        credential_id=f"cred-{user_id}",
        user_id=user_id,
        provider="local",
        provider_user_id=user_id,  # user_id stored in DB
        hashed_secret="hashed:password123",
    )
    user.add_credential(credential)
    return user


class TestSqlAlchemyUnitOfWork:
    def test_commit_persists_user(
        self, auth_session_factory: sessionmaker[Session]
    ) -> None:
        uow = SqlAlchemyUnitOfWork(auth_session_factory)
        user = _make_user()

        with uow:
            uow.users.save(user)
            uow.commit()

        # Verify data was committed by reading with a new UoW
        with uow:
            found = uow.users.find_by_id("user-1")
            assert found is not None
            assert found.email == "alice@example.com"
            assert len(found.credentials) == 1

    def test_rollback_on_exit_without_commit(
        self, auth_session_factory: sessionmaker[Session]
    ) -> None:
        uow = SqlAlchemyUnitOfWork(auth_session_factory)
        user = _make_user()

        with uow:
            uow.users.save(user)
            # No commit — exit should rollback

        with uow:
            found = uow.users.find_by_id("user-1")
            assert found is None

    def test_explicit_rollback_discards_changes(
        self, auth_session_factory: sessionmaker[Session]
    ) -> None:
        uow = SqlAlchemyUnitOfWork(auth_session_factory)
        user = _make_user()

        with uow:
            uow.users.save(user)
            uow.rollback()

        with uow:
            found = uow.users.find_by_id("user-1")
            assert found is None

    def test_uow_provides_user_repository(
        self, auth_session_factory: sessionmaker[Session]
    ) -> None:
        uow = SqlAlchemyUnitOfWork(auth_session_factory)
        with uow:
            assert hasattr(uow, "users")
            assert uow.users is not None
