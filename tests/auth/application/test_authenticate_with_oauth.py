"""Tests for AuthenticateWithOAuth use case — TDD Red phase.

Scenarios:
1. New user (email not in system) → creates User + google Credential → returns token
2. Existing user without google credential → links google Credential → returns token
3. Existing user already has google credential → returns token (login)
4. Inactive user → raises ValueError
5. OAuthClient raises OAuthError → propagates
6. Transaction is committed on success
"""

import pytest

from auth.application.authenticate_with_oauth import AuthenticateWithOAuthUseCase
from auth.domain.oauth import OAuthError, OAuthUserInfo
from auth.domain.user import Credential, User
from tests.auth.fakes.fake_unit_of_work import (
    FakeOAuthClient,
    FakeTokenService,
    FakeUnitOfWork,
)

GOOGLE_USER_INFO = OAuthUserInfo(
    provider="google",
    provider_user_id="google-sub-123",
    email="alice@example.com",
    display_name="Alice from Google",
)


def _make_use_case(
    uow: FakeUnitOfWork,
    oauth_client: FakeOAuthClient | None = None,
    token_service: FakeTokenService | None = None,
) -> AuthenticateWithOAuthUseCase:
    return AuthenticateWithOAuthUseCase(
        uow=uow,
        oauth_client=oauth_client or FakeOAuthClient(user_info=GOOGLE_USER_INFO),
        token_service=token_service or FakeTokenService(),
    )


class TestAuthenticateWithOAuthNewUser:
    """When no user with the OAuth email exists, create a new user."""

    def test_creates_user_with_oauth_email_and_display_name(self) -> None:
        uow = FakeUnitOfWork()
        use_case = _make_use_case(uow)

        use_case.execute(code="auth-code-123")

        user = uow.users.find_by_email("alice@example.com")
        assert user is not None
        assert user.email == "alice@example.com"
        assert user.display_name == "Alice from Google"

    def test_creates_google_credential_on_new_user(self) -> None:
        uow = FakeUnitOfWork()
        use_case = _make_use_case(uow)

        use_case.execute(code="auth-code-123")

        user = uow.users.find_by_email("alice@example.com")
        assert user is not None
        cred = user.find_credential_by_provider("google")
        assert cred is not None
        assert cred.provider_user_id == "google-sub-123"
        assert cred.hashed_secret is None

    def test_returns_access_token_for_new_user(self) -> None:
        uow = FakeUnitOfWork()
        use_case = _make_use_case(uow)

        token = use_case.execute(code="auth-code-123")

        # FakeTokenService returns "fake-token:<user_id>"
        assert token.startswith("fake-token:")

    def test_new_user_is_active(self) -> None:
        uow = FakeUnitOfWork()
        use_case = _make_use_case(uow)

        use_case.execute(code="auth-code-123")

        user = uow.users.find_by_email("alice@example.com")
        assert user is not None
        assert user.is_active is True


class TestAuthenticateWithOAuthExistingUserNoGoogleCredential:
    """When a user with the same email exists but has no google credential,
    link the google credential to the existing user."""

    def test_links_google_credential_to_existing_user(self) -> None:
        uow = FakeUnitOfWork()
        # Pre-create a user with only local credential
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        local_cred = Credential(
            credential_id="cred-local",
            user_id="u1",
            provider="local",
            provider_user_id="alice@example.com",
            hashed_secret="hashed:secret123",
        )
        user.add_credential(local_cred)
        uow.users.save(user)

        use_case = _make_use_case(uow)
        use_case.execute(code="auth-code-123")

        updated_user = uow.users.find_by_email("alice@example.com")
        assert updated_user is not None
        assert updated_user.user_id == "u1"  # same user, not a new one
        google_cred = updated_user.find_credential_by_provider("google")
        assert google_cred is not None
        assert google_cred.provider_user_id == "google-sub-123"

    def test_returns_token_for_existing_user(self) -> None:
        uow = FakeUnitOfWork()
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        local_cred = Credential(
            credential_id="cred-local",
            user_id="u1",
            provider="local",
            provider_user_id="alice@example.com",
            hashed_secret="hashed:secret123",
        )
        user.add_credential(local_cred)
        uow.users.save(user)

        use_case = _make_use_case(uow)
        token = use_case.execute(code="auth-code-123")

        assert token == "fake-token:u1"

    def test_preserves_existing_local_credential(self) -> None:
        uow = FakeUnitOfWork()
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        local_cred = Credential(
            credential_id="cred-local",
            user_id="u1",
            provider="local",
            provider_user_id="alice@example.com",
            hashed_secret="hashed:secret123",
        )
        user.add_credential(local_cred)
        uow.users.save(user)

        use_case = _make_use_case(uow)
        use_case.execute(code="auth-code-123")

        updated_user = uow.users.find_by_email("alice@example.com")
        assert updated_user is not None
        assert updated_user.find_credential_by_provider("local") is not None
        assert updated_user.find_credential_by_provider("google") is not None
        assert len(updated_user.credentials) == 2


class TestAuthenticateWithOAuthExistingUserWithGoogleCredential:
    """When a user already has a google credential, just return a token (login)."""

    def test_returns_token_without_creating_new_credential(self) -> None:
        uow = FakeUnitOfWork()
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        google_cred = Credential(
            credential_id="cred-google",
            user_id="u1",
            provider="google",
            provider_user_id="google-sub-123",
            hashed_secret=None,
        )
        user.add_credential(google_cred)
        uow.users.save(user)

        use_case = _make_use_case(uow)
        token = use_case.execute(code="auth-code-123")

        assert token == "fake-token:u1"
        # Still only one google credential, no duplicates
        assert len([c for c in user.credentials if c.provider == "google"]) == 1


class TestAuthenticateWithOAuthErrorCases:
    """Error scenarios for OAuth authentication."""

    def test_raises_when_user_is_inactive(self) -> None:
        uow = FakeUnitOfWork()
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        google_cred = Credential(
            credential_id="cred-google",
            user_id="u1",
            provider="google",
            provider_user_id="google-sub-123",
            hashed_secret=None,
        )
        user.add_credential(google_cred)
        user.deactivate()
        uow.users.save(user)

        use_case = _make_use_case(uow)

        with pytest.raises(ValueError, match="User account is inactive"):
            use_case.execute(code="auth-code-123")

    def test_propagates_oauth_error_from_exchange_code(self) -> None:
        uow = FakeUnitOfWork()
        oauth_client = FakeOAuthClient(error=OAuthError("Invalid authorization code"))
        use_case = _make_use_case(uow, oauth_client=oauth_client)

        with pytest.raises(OAuthError, match="Invalid authorization code"):
            use_case.execute(code="bad-code")

    def test_propagates_oauth_error_from_get_user_info(self) -> None:
        """OAuthClient that succeeds on exchange_code but fails on get_user_info."""
        uow = FakeUnitOfWork()
        # We need a client that raises only on get_user_info, not exchange_code.
        # FakeOAuthClient raises on both if error is set, so we create a custom one.

        class FailOnUserInfoClient:
            def build_authorization_url(self, state: str) -> str:
                return "https://example.com"

            def exchange_code(self, code: str) -> str:
                return "access-token"

            def get_user_info(self, access_token: str) -> OAuthUserInfo:
                raise OAuthError("Failed to fetch user info")

        use_case = AuthenticateWithOAuthUseCase(
            uow=uow,
            oauth_client=FailOnUserInfoClient(),
            token_service=FakeTokenService(),
        )

        with pytest.raises(OAuthError, match="Failed to fetch user info"):
            use_case.execute(code="valid-code")


class TestAuthenticateWithOAuthTransaction:
    """Verify that the use case commits the transaction."""

    def test_commits_transaction_on_success(self) -> None:
        uow = FakeUnitOfWork()
        use_case = _make_use_case(uow)

        use_case.execute(code="auth-code-123")

        assert uow.committed is True

    def test_exchanges_the_authorization_code(self) -> None:
        uow = FakeUnitOfWork()
        oauth_client = FakeOAuthClient(user_info=GOOGLE_USER_INFO)
        use_case = _make_use_case(uow, oauth_client=oauth_client)

        use_case.execute(code="auth-code-123")

        assert oauth_client.exchanged_codes == ["auth-code-123"]
