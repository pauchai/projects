"""Tests for SetPasswordUseCase — TDD.

Scenarios:
1. Happy path: sets local credential for a user who only has OAuth credentials.
2. Happy path: provider_user_id is set to user_id (not email).
3. Happy path: password is hashed before storage.
4. Happy path: transaction is committed on success.
5. Error: user not found → LookupError.
6. Error: user already has local credentials → ValueError.
"""

import pytest

from auth.application.set_password import SetPasswordUseCase
from auth.domain.user import Credential, User
from tests.auth.fakes.fake_unit_of_work import FakePasswordHasher, FakeUnitOfWork


def _make_user_with_google(
    user_id: str = "u1",
    email: str = "alice@example.com",
) -> User:
    """Create a user with only a Google credential (no local)."""
    user = User(user_id=user_id, email=email, display_name="Alice")
    google_cred = Credential(
        credential_id="cred-google",
        user_id=user_id,
        provider="google",
        provider_user_id="google-sub-123",
        hashed_secret=None,
    )
    user.add_credential(google_cred)
    return user


def _make_user_with_local(
    user_id: str = "u1",
    email: str = "alice@example.com",
) -> User:
    """Create a user who already has a local credential."""
    user = User(user_id=user_id, email=email, display_name="Alice")
    local_cred = Credential(
        credential_id="cred-local",
        user_id=user_id,
        provider="local",
        provider_user_id=user_id,
        hashed_secret="hashed:existing_password",
    )
    user.add_credential(local_cred)
    return user


class TestSetPasswordUseCaseHappyPath:
    """Successfully set a password for a user without local credentials."""

    def test_adds_local_credential_to_user(self) -> None:
        uow = FakeUnitOfWork()
        user = _make_user_with_google()
        uow.users.save(user)

        use_case = SetPasswordUseCase(uow, FakePasswordHasher())
        use_case.execute(user_id="u1", password="newpass123")

        saved = uow.users.find_by_id("u1")
        assert saved is not None
        assert saved.has_credential_for_provider("local") is True

    def test_provider_user_id_is_user_id_not_email(self) -> None:
        uow = FakeUnitOfWork()
        user = _make_user_with_google()
        uow.users.save(user)

        use_case = SetPasswordUseCase(uow, FakePasswordHasher())
        use_case.execute(user_id="u1", password="newpass123")

        saved = uow.users.find_by_id("u1")
        assert saved is not None
        local_cred = saved.find_credential_by_provider("local")
        assert local_cred is not None
        assert local_cred.provider_user_id == "u1"  # user_id, not email

    def test_password_is_hashed(self) -> None:
        uow = FakeUnitOfWork()
        user = _make_user_with_google()
        uow.users.save(user)

        use_case = SetPasswordUseCase(uow, FakePasswordHasher())
        use_case.execute(user_id="u1", password="newpass123")

        saved = uow.users.find_by_id("u1")
        assert saved is not None
        local_cred = saved.find_credential_by_provider("local")
        assert local_cred is not None
        assert local_cred.hashed_secret == "hashed:newpass123"

    def test_preserves_existing_oauth_credentials(self) -> None:
        uow = FakeUnitOfWork()
        user = _make_user_with_google()
        uow.users.save(user)

        use_case = SetPasswordUseCase(uow, FakePasswordHasher())
        use_case.execute(user_id="u1", password="newpass123")

        saved = uow.users.find_by_id("u1")
        assert saved is not None
        assert len(saved.credentials) == 2
        assert saved.has_credential_for_provider("google") is True

    def test_commits_transaction(self) -> None:
        uow = FakeUnitOfWork()
        user = _make_user_with_google()
        uow.users.save(user)

        use_case = SetPasswordUseCase(uow, FakePasswordHasher())
        use_case.execute(user_id="u1", password="newpass123")

        assert uow.committed is True


class TestSetPasswordUseCaseErrorCases:
    """Error scenarios for SetPasswordUseCase."""

    def test_raises_lookup_error_when_user_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = SetPasswordUseCase(uow, FakePasswordHasher())

        with pytest.raises(LookupError, match="User nonexistent not found"):
            use_case.execute(user_id="nonexistent", password="pass123")

    def test_raises_value_error_when_user_already_has_local(self) -> None:
        uow = FakeUnitOfWork()
        user = _make_user_with_local()
        uow.users.save(user)

        use_case = SetPasswordUseCase(uow, FakePasswordHasher())

        with pytest.raises(ValueError, match="already has local credentials"):
            use_case.execute(user_id="u1", password="newpass123")

    def test_does_not_commit_on_error(self) -> None:
        uow = FakeUnitOfWork()
        # No user → LookupError
        use_case = SetPasswordUseCase(uow, FakePasswordHasher())

        with pytest.raises(LookupError):
            use_case.execute(user_id="nonexistent", password="pass123")

        assert uow.committed is False
