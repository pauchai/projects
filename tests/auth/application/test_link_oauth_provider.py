"""Tests for LinkOAuthProviderUseCase — TDD.

Scenarios:
1. Happy path: links Google credential to user with only local credential.
2. Happy path: links Telegram credential to user with local + Google.
3. Error: OAuth client fails on exchange_code → OAuthError propagates.
4. Error: OAuth client fails on get_user_info → OAuthError propagates.
5. Error: OAuth account already belongs to a different user → OAuthAccountAlreadyLinkedError.
6. Error: User already has a credential for this provider → ValueError.
7. Error: User not found → LookupError.
8. Error: User is inactive → ValueError.
9. Commit: Transaction is committed on success.
10. Idempotency: Same user owns the OAuth account → raises ValueError
    (user already has credential for the provider), not conflict error.
"""

import pytest

from auth.application.link_oauth_provider import LinkOAuthProviderUseCase
from auth.domain.oauth import OAuthAccountAlreadyLinkedError, OAuthError, OAuthUserInfo
from auth.domain.user import Credential, User
from tests.auth.fakes.fake_unit_of_work import (
    FakeOAuthClient,
    FakeUnitOfWork,
)

GOOGLE_USER_INFO = OAuthUserInfo(
    provider="google",
    provider_user_id="google-sub-123",
    email="alice@google.com",
    display_name="Alice Google",
)

TELEGRAM_USER_INFO = OAuthUserInfo(
    provider="telegram",
    provider_user_id="tg-user-456",
    email="alice@telegram.org",
    display_name="Alice Telegram",
)


def _make_user_with_local(
    user_id: str = "u1",
    email: str = "alice@example.com",
    display_name: str = "Alice",
) -> User:
    """Create a user with a local (email+password) credential."""
    user = User(user_id=user_id, email=email, display_name=display_name)
    credential = Credential(
        credential_id=f"cred-local-{user_id}",
        user_id=user_id,
        provider="local",
        provider_user_id=email,
        hashed_secret="hashed:password123",
    )
    user.add_credential(credential)
    return user


def _make_use_case(
    uow: FakeUnitOfWork,
    oauth_client: FakeOAuthClient | None = None,
) -> LinkOAuthProviderUseCase:
    return LinkOAuthProviderUseCase(
        uow=uow,
        oauth_client=oauth_client or FakeOAuthClient(user_info=GOOGLE_USER_INFO),
    )


class TestLinkOAuthProviderHappyPath:
    """Successfully link an OAuth provider to an existing user."""

    def test_links_google_credential_to_local_user(self) -> None:
        uow = FakeUnitOfWork()
        user = _make_user_with_local()
        uow.users.save(user)

        use_case = _make_use_case(uow)
        use_case.execute(user_id="u1", code="auth-code-123")

        updated = uow.users.find_by_id("u1")
        assert updated is not None
        google_cred = updated.find_credential_by_provider("google")
        assert google_cred is not None
        assert google_cred.provider_user_id == "google-sub-123"
        assert google_cred.hashed_secret is None

    def test_preserves_existing_local_credential(self) -> None:
        uow = FakeUnitOfWork()
        user = _make_user_with_local()
        uow.users.save(user)

        use_case = _make_use_case(uow)
        use_case.execute(user_id="u1", code="auth-code-123")

        updated = uow.users.find_by_id("u1")
        assert updated is not None
        assert updated.find_credential_by_provider("local") is not None
        assert len(updated.credentials) == 2

    def test_links_telegram_to_user_with_local_and_google(self) -> None:
        uow = FakeUnitOfWork()
        user = _make_user_with_local()
        google_cred = Credential(
            credential_id="cred-google",
            user_id="u1",
            provider="google",
            provider_user_id="google-sub-999",
            hashed_secret=None,
        )
        user.add_credential(google_cred)
        uow.users.save(user)

        oauth_client = FakeOAuthClient(user_info=TELEGRAM_USER_INFO)
        use_case = _make_use_case(uow, oauth_client=oauth_client)
        use_case.execute(user_id="u1", code="tg-code")

        updated = uow.users.find_by_id("u1")
        assert updated is not None
        assert len(updated.credentials) == 3
        assert updated.find_credential_by_provider("telegram") is not None

    def test_exchanges_the_authorization_code(self) -> None:
        uow = FakeUnitOfWork()
        user = _make_user_with_local()
        uow.users.save(user)

        oauth_client = FakeOAuthClient(user_info=GOOGLE_USER_INFO)
        use_case = _make_use_case(uow, oauth_client=oauth_client)
        use_case.execute(user_id="u1", code="my-auth-code")

        assert oauth_client.exchanged_codes == ["my-auth-code"]


class TestLinkOAuthProviderErrorCases:
    """Error scenarios for linking an OAuth provider."""

    def test_raises_lookup_error_when_user_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = _make_use_case(uow)

        with pytest.raises(LookupError, match="User nonexistent not found"):
            use_case.execute(user_id="nonexistent", code="auth-code")

    def test_raises_value_error_when_user_is_inactive(self) -> None:
        uow = FakeUnitOfWork()
        user = _make_user_with_local()
        user.deactivate()
        uow.users.save(user)

        use_case = _make_use_case(uow)

        with pytest.raises(ValueError, match="User account is inactive"):
            use_case.execute(user_id="u1", code="auth-code")

    def test_raises_oauth_error_on_exchange_code_failure(self) -> None:
        uow = FakeUnitOfWork()
        user = _make_user_with_local()
        uow.users.save(user)

        oauth_client = FakeOAuthClient(error=OAuthError("Invalid code"))
        use_case = _make_use_case(uow, oauth_client=oauth_client)

        with pytest.raises(OAuthError, match="Invalid code"):
            use_case.execute(user_id="u1", code="bad-code")

    def test_raises_value_error_when_provider_already_linked(self) -> None:
        uow = FakeUnitOfWork()
        user = _make_user_with_local()
        google_cred = Credential(
            credential_id="cred-google",
            user_id="u1",
            provider="google",
            provider_user_id="google-sub-existing",
            hashed_secret=None,
        )
        user.add_credential(google_cred)
        uow.users.save(user)

        use_case = _make_use_case(uow)

        with pytest.raises(ValueError, match="already has a credential for google"):
            use_case.execute(user_id="u1", code="auth-code")

    def test_raises_conflict_when_oauth_account_belongs_to_another_user(self) -> None:
        uow = FakeUnitOfWork()
        # User A wants to link Google
        user_a = _make_user_with_local(
            user_id="ua", email="a@example.com", display_name="A"
        )
        uow.users.save(user_a)

        # User B already owns this Google account
        user_b = _make_user_with_local(
            user_id="ub", email="b@example.com", display_name="B"
        )
        google_cred_b = Credential(
            credential_id="cred-google-b",
            user_id="ub",
            provider="google",
            provider_user_id="google-sub-123",  # same as GOOGLE_USER_INFO
            hashed_secret=None,
        )
        user_b.add_credential(google_cred_b)
        uow.users.save(user_b)

        use_case = _make_use_case(uow)

        with pytest.raises(OAuthAccountAlreadyLinkedError) as exc_info:
            use_case.execute(user_id="ua", code="auth-code")

        assert exc_info.value.provider == "google"
        assert exc_info.value.owner_user_id == "ub"


class TestLinkOAuthProviderTransaction:
    """Verify transaction behavior."""

    def test_commits_on_success(self) -> None:
        uow = FakeUnitOfWork()
        user = _make_user_with_local()
        uow.users.save(user)

        use_case = _make_use_case(uow)
        use_case.execute(user_id="u1", code="auth-code")

        assert uow.committed is True

    def test_does_not_commit_on_error(self) -> None:
        uow = FakeUnitOfWork()
        # No user → LookupError
        use_case = _make_use_case(uow)

        with pytest.raises(LookupError):
            use_case.execute(user_id="nonexistent", code="auth-code")

        assert uow.committed is False
