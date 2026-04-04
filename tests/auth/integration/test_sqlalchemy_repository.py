"""Integration tests for SqlAlchemyUserRepository.

Tests verify that save/find operations round-trip correctly through PostgreSQL.
Each test is isolated via SAVEPOINT (see conftest.py).
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from auth.domain.user import Credential, User
from auth.infrastructure.sqlalchemy_repository import SqlAlchemyUserRepository


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
        provider_user_id=email,
        hashed_secret="hashed:password123",
    )
    user.add_credential(credential)
    return user


class TestSqlAlchemyUserRepositorySaveAndFindById:
    def test_save_and_find_by_id_round_trip(self, auth_session: Session) -> None:
        repo = SqlAlchemyUserRepository(auth_session)
        user = _make_user()

        repo.save(user)
        auth_session.commit()

        found = repo.find_by_id("user-1")
        assert found is not None
        assert found.user_id == "user-1"
        assert found.email == "alice@example.com"
        assert found.display_name == "Alice"
        assert found.is_active is True
        assert isinstance(found.created_at, datetime)

    def test_find_by_id_returns_none_when_not_found(
        self, auth_session: Session
    ) -> None:
        repo = SqlAlchemyUserRepository(auth_session)
        assert repo.find_by_id("nonexistent") is None

    def test_save_persists_credentials(self, auth_session: Session) -> None:
        repo = SqlAlchemyUserRepository(auth_session)
        user = _make_user()

        repo.save(user)
        auth_session.commit()

        found = repo.find_by_id("user-1")
        assert found is not None
        assert len(found.credentials) == 1
        cred = found.credentials[0]
        assert cred.credential_id == "cred-user-1"
        assert cred.provider == "local"
        assert cred.provider_user_id == "alice@example.com"
        assert cred.hashed_secret == "hashed:password123"
        assert isinstance(cred.created_at, datetime)


class TestSqlAlchemyUserRepositoryFindByEmail:
    def test_find_by_email_returns_user(self, auth_session: Session) -> None:
        repo = SqlAlchemyUserRepository(auth_session)
        user = _make_user()
        repo.save(user)
        auth_session.commit()

        found = repo.find_by_email("alice@example.com")
        assert found is not None
        assert found.user_id == "user-1"
        assert found.email == "alice@example.com"

    def test_find_by_email_normalizes_input(self, auth_session: Session) -> None:
        repo = SqlAlchemyUserRepository(auth_session)
        user = _make_user()
        repo.save(user)
        auth_session.commit()

        found = repo.find_by_email("  Alice@Example.COM  ")
        assert found is not None
        assert found.user_id == "user-1"

    def test_find_by_email_returns_none_when_not_found(
        self, auth_session: Session
    ) -> None:
        repo = SqlAlchemyUserRepository(auth_session)
        assert repo.find_by_email("nobody@example.com") is None

    def test_find_by_email_includes_credentials(self, auth_session: Session) -> None:
        repo = SqlAlchemyUserRepository(auth_session)
        user = _make_user()
        repo.save(user)
        auth_session.commit()

        found = repo.find_by_email("alice@example.com")
        assert found is not None
        assert len(found.credentials) == 1


class TestSqlAlchemyUserRepositoryUpdate:
    def test_save_updates_existing_user(self, auth_session: Session) -> None:
        repo = SqlAlchemyUserRepository(auth_session)
        user = _make_user()
        repo.save(user)
        auth_session.commit()

        # Mutate and re-save
        user.deactivate()
        repo.save(user)
        auth_session.commit()

        found = repo.find_by_id("user-1")
        assert found is not None
        assert found.is_active is False

    def test_save_adds_new_credential_to_existing_user(
        self, auth_session: Session
    ) -> None:
        repo = SqlAlchemyUserRepository(auth_session)
        user = _make_user()
        repo.save(user)
        auth_session.commit()

        # Add a second credential (e.g., Google OAuth)
        google_cred = Credential(
            credential_id="cred-2",
            user_id="user-1",
            provider="google",
            provider_user_id="google-sub-123",
            hashed_secret=None,
        )
        user.add_credential(google_cred)
        repo.save(user)
        auth_session.commit()

        found = repo.find_by_id("user-1")
        assert found is not None
        assert len(found.credentials) == 2
        providers = {c.provider for c in found.credentials}
        assert providers == {"local", "google"}


class TestSqlAlchemyUserRepositoryMultipleUsers:
    def test_multiple_users_are_independent(self, auth_session: Session) -> None:
        repo = SqlAlchemyUserRepository(auth_session)

        user1 = _make_user(user_id="u1", email="a@test.com", display_name="A")
        user2 = _make_user(user_id="u2", email="b@test.com", display_name="B")

        repo.save(user1)
        repo.save(user2)
        auth_session.commit()

        found1 = repo.find_by_id("u1")
        found2 = repo.find_by_id("u2")
        assert found1 is not None
        assert found2 is not None
        assert found1.email == "a@test.com"
        assert found2.email == "b@test.com"
        assert len(found1.credentials) == 1
        assert len(found2.credentials) == 1
