"""Tests for Authenticate use case."""

import pytest

from auth.application.authenticate import AuthenticateUseCase
from auth.application.register_user import RegisterUserUseCase
from tests.auth.fakes.fake_unit_of_work import (
    FakeUnitOfWork,
    FakePasswordHasher,
    FakeTokenService,
)


def _register_user(
    uow: FakeUnitOfWork,
    hasher: FakePasswordHasher,
    user_id: str = "u1",
    email: str = "alice@example.com",
    password: str = "secret123",
    display_name: str = "Alice",
) -> str:
    """Helper to register a user for authentication tests."""
    use_case = RegisterUserUseCase(uow=uow, password_hasher=hasher)
    return use_case.execute(
        user_id=user_id,
        email=email,
        password=password,
        display_name=display_name,
    )


class TestAuthenticateUseCase:
    """Authenticate verifies credentials and returns a JWT token."""

    def test_returns_token_on_valid_credentials(self) -> None:
        uow = FakeUnitOfWork()
        hasher = FakePasswordHasher()
        token_service = FakeTokenService()
        _register_user(uow, hasher)

        use_case = AuthenticateUseCase(
            uow=uow, password_hasher=hasher, token_service=token_service
        )
        token = use_case.execute(email="alice@example.com", password="secret123")

        assert token == "fake-token:u1"

    def test_raises_on_unknown_email(self) -> None:
        uow = FakeUnitOfWork()
        hasher = FakePasswordHasher()
        token_service = FakeTokenService()

        use_case = AuthenticateUseCase(
            uow=uow, password_hasher=hasher, token_service=token_service
        )

        with pytest.raises(ValueError, match="Invalid email or password"):
            use_case.execute(email="unknown@example.com", password="secret123")

    def test_raises_on_wrong_password(self) -> None:
        uow = FakeUnitOfWork()
        hasher = FakePasswordHasher()
        token_service = FakeTokenService()
        _register_user(uow, hasher)

        use_case = AuthenticateUseCase(
            uow=uow, password_hasher=hasher, token_service=token_service
        )

        with pytest.raises(ValueError, match="Invalid email or password"):
            use_case.execute(email="alice@example.com", password="wrong_password")

    def test_raises_when_user_has_no_local_credential(self) -> None:
        uow = FakeUnitOfWork()
        hasher = FakePasswordHasher()
        token_service = FakeTokenService()

        # Manually create a user with only Google credential (no local)
        from auth.domain.user import User, Credential

        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        google_cred = Credential(
            credential_id="cred-g",
            user_id="u1",
            provider="google",
            provider_user_id="google-sub-123",
            hashed_secret=None,
        )
        user.add_credential(google_cred)
        uow.users.save(user)

        use_case = AuthenticateUseCase(
            uow=uow, password_hasher=hasher, token_service=token_service
        )

        with pytest.raises(ValueError, match="Invalid email or password"):
            use_case.execute(email="alice@example.com", password="secret123")

    def test_raises_when_user_is_inactive(self) -> None:
        uow = FakeUnitOfWork()
        hasher = FakePasswordHasher()
        token_service = FakeTokenService()
        _register_user(uow, hasher)

        # Deactivate the user
        user = uow.users.find_by_email("alice@example.com")
        assert user is not None
        user.deactivate()

        use_case = AuthenticateUseCase(
            uow=uow, password_hasher=hasher, token_service=token_service
        )

        with pytest.raises(ValueError, match="User account is inactive"):
            use_case.execute(email="alice@example.com", password="secret123")

    def test_email_is_case_insensitive(self) -> None:
        uow = FakeUnitOfWork()
        hasher = FakePasswordHasher()
        token_service = FakeTokenService()
        _register_user(uow, hasher, email="Alice@Example.COM")

        use_case = AuthenticateUseCase(
            uow=uow, password_hasher=hasher, token_service=token_service
        )
        token = use_case.execute(email="alice@example.com", password="secret123")

        assert token == "fake-token:u1"
