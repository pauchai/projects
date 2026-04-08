"""Tests for OAuthCredentialLinkingService — domain service.

Scenarios:
1. Successfully links a new OAuth credential to the user.
2. Sets correct provider, provider_user_id, and user_id on the credential.
3. Raises ValueError if user already has credential for this provider.
4. Raises OAuthAccountAlreadyLinkedError if OAuth account belongs to another user.
5. Does not raise when OAuth account belongs to the same user (idempotent check).
6. New credential has no hashed_secret (OAuth credentials don't use passwords).
"""

import pytest

from auth.domain.oauth import OAuthAccountAlreadyLinkedError, OAuthUserInfo
from auth.domain.oauth_linking_service import OAuthCredentialLinkingService
from auth.domain.user import Credential, User


def _make_user(
    user_id: str = "user-1",
    email: str = "alice@example.com",
    providers: list[str] | None = None,
) -> User:
    """Helper: create a User with optional pre-existing credentials."""
    user = User(user_id=user_id, email=email, display_name="Alice")
    for provider in providers or []:
        cred = Credential(
            credential_id=f"cred-{user_id}-{provider}",
            user_id=user_id,
            provider=provider,
            provider_user_id=f"{provider}-ext-{user_id}",
            hashed_secret="hashed" if provider == "local" else None,
        )
        user.add_credential(cred)
    return user


GOOGLE_INFO = OAuthUserInfo(
    provider="google",
    provider_user_id="google-ext-new",
    email="alice@gmail.com",
    display_name="Alice Google",
)


class TestLinkCredentialSuccessfully:
    """When the user has no credential for this provider and no conflict exists."""

    def test_adds_credential_to_user(self) -> None:
        user = _make_user(providers=["local"])
        service = OAuthCredentialLinkingService()

        service.link(user=user, oauth_info=GOOGLE_INFO, existing_owner=None)

        assert user.has_credential_for_provider("google")

    def test_credential_has_correct_provider_user_id(self) -> None:
        user = _make_user(providers=["local"])
        service = OAuthCredentialLinkingService()

        service.link(user=user, oauth_info=GOOGLE_INFO, existing_owner=None)

        cred = user.find_credential_by_provider("google")
        assert cred is not None
        assert cred.provider_user_id == "google-ext-new"

    def test_credential_has_correct_user_id(self) -> None:
        user = _make_user(providers=["local"])
        service = OAuthCredentialLinkingService()

        service.link(user=user, oauth_info=GOOGLE_INFO, existing_owner=None)

        cred = user.find_credential_by_provider("google")
        assert cred is not None
        assert cred.user_id == "user-1"

    def test_credential_has_no_hashed_secret(self) -> None:
        user = _make_user(providers=["local"])
        service = OAuthCredentialLinkingService()

        service.link(user=user, oauth_info=GOOGLE_INFO, existing_owner=None)

        cred = user.find_credential_by_provider("google")
        assert cred is not None
        assert cred.hashed_secret is None

    def test_credential_count_increases_by_one(self) -> None:
        user = _make_user(providers=["local"])
        service = OAuthCredentialLinkingService()

        before = len(user.credentials)
        service.link(user=user, oauth_info=GOOGLE_INFO, existing_owner=None)

        assert len(user.credentials) == before + 1


class TestLinkCredentialAlreadyHasProvider:
    """When the user already has a credential for the same provider."""

    def test_raises_value_error(self) -> None:
        user = _make_user(providers=["local", "google"])
        service = OAuthCredentialLinkingService()

        with pytest.raises(ValueError, match="already has a credential for google"):
            service.link(user=user, oauth_info=GOOGLE_INFO, existing_owner=None)


class TestLinkCredentialOAuthAccountConflict:
    """When the OAuth account is already linked to a different user."""

    def test_raises_already_linked_error(self) -> None:
        user = _make_user(user_id="user-1", providers=["local"])
        other_user = _make_user(user_id="user-2", email="bob@example.com")
        service = OAuthCredentialLinkingService()

        with pytest.raises(OAuthAccountAlreadyLinkedError) as exc_info:
            service.link(user=user, oauth_info=GOOGLE_INFO, existing_owner=other_user)

        assert exc_info.value.provider == "google"
        assert exc_info.value.owner_user_id == "user-2"

    def test_error_message_contains_provider_name(self) -> None:
        user = _make_user(user_id="user-1", providers=["local"])
        other_user = _make_user(user_id="user-2", email="bob@example.com")
        service = OAuthCredentialLinkingService()

        with pytest.raises(
            OAuthAccountAlreadyLinkedError,
            match="google account is already connected",
        ):
            service.link(user=user, oauth_info=GOOGLE_INFO, existing_owner=other_user)


class TestLinkCredentialSameOwner:
    """When existing_owner is the same user — no conflict (idempotent)."""

    def test_does_not_raise_when_owner_is_same_user(self) -> None:
        user = _make_user(user_id="user-1", providers=["local"])
        service = OAuthCredentialLinkingService()

        # existing_owner is the same user — should NOT raise conflict
        # but should still raise "already has credential" if provider exists
        # Here the user does NOT have google yet, so it should succeed
        service.link(user=user, oauth_info=GOOGLE_INFO, existing_owner=user)

        assert user.has_credential_for_provider("google")
