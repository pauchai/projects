"""Tests for ViewUserCredentialsUseCase."""

import pytest

from auth.application.view_user_credentials import (
    ViewUserCredentialsResult,
    ViewUserCredentialsUseCase,
)
from auth.domain.user import Credential, User
from tests.auth.fakes.fake_unit_of_work import FakeUnitOfWork


def _make_user_with_credentials(
    *providers: str,
    user_id: str = "u1",
    email: str = "alice@example.com",
) -> User:
    """Create a user and add credentials for each provider."""
    user = User(user_id=user_id, email=email, display_name="Alice")
    for i, provider in enumerate(providers):
        hashed_secret = "hashed_pw" if provider == "local" else None
        provider_user_id = email if provider == "local" else f"{provider}-id-{i}"
        cred = Credential(
            credential_id=f"cred-{provider}",
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            hashed_secret=hashed_secret,
        )
        user.add_credential(cred)
    return user


class TestViewUserCredentialsUseCase:
    """Use case returns credential summaries for an authenticated user."""

    def test_returns_credentials_for_active_user(self) -> None:
        uow = FakeUnitOfWork()
        user = _make_user_with_credentials("local", "google")
        uow.users.save(user)

        use_case = ViewUserCredentialsUseCase(uow)
        result = use_case.execute("u1")

        assert isinstance(result, ViewUserCredentialsResult)
        assert result.user_email == "alice@example.com"
        assert result.user_display_name == "Alice"
        assert result.total_count == 2
        assert len(result.credentials) == 2

    def test_credentials_contain_expected_fields(self) -> None:
        uow = FakeUnitOfWork()
        user = _make_user_with_credentials("local")
        uow.users.save(user)

        use_case = ViewUserCredentialsUseCase(uow)
        result = use_case.execute("u1")

        cred = result.credentials[0]
        assert cred.credential_id == "cred-local"
        assert cred.provider == "local"
        assert cred.provider_display_name == "Email & Password"
        assert cred.provider_user_id == "alice@example.com"

    def test_has_local_credential_is_true_when_present(self) -> None:
        uow = FakeUnitOfWork()
        user = _make_user_with_credentials("local", "google")
        uow.users.save(user)

        use_case = ViewUserCredentialsUseCase(uow)
        result = use_case.execute("u1")
        assert result.has_local_credential is True

    def test_has_local_credential_is_false_when_absent(self) -> None:
        uow = FakeUnitOfWork()
        user = _make_user_with_credentials("google")
        uow.users.save(user)

        use_case = ViewUserCredentialsUseCase(uow)
        result = use_case.execute("u1")
        assert result.has_local_credential is False

    def test_raises_lookup_error_when_user_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = ViewUserCredentialsUseCase(uow)

        with pytest.raises(LookupError, match="User nonexistent not found"):
            use_case.execute("nonexistent")

    def test_raises_value_error_when_user_inactive(self) -> None:
        uow = FakeUnitOfWork()
        user = _make_user_with_credentials("local")
        user.deactivate()
        uow.users.save(user)

        use_case = ViewUserCredentialsUseCase(uow)

        with pytest.raises(ValueError, match="User account is inactive"):
            use_case.execute("u1")

    def test_returns_all_three_providers(self) -> None:
        uow = FakeUnitOfWork()
        user = _make_user_with_credentials("local", "google", "telegram")
        uow.users.save(user)

        use_case = ViewUserCredentialsUseCase(uow)
        result = use_case.execute("u1")

        providers = {c.provider for c in result.credentials}
        assert providers == {"local", "google", "telegram"}
        assert result.total_count == 3
