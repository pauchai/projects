"""Tests for User credential summary and management methods."""

import pytest

from auth.domain.user import CredentialSummary, Credential, User


class TestCredentialSummary:
    """CredentialSummary is a read-only value object for UI display."""

    def test_stores_all_fields(self) -> None:
        summary = CredentialSummary(
            credential_id="cred-1",
            provider="local",
            provider_display_name="Email & Password",
            provider_user_id="alice@example.com",
            is_removable=False,
        )
        assert summary.credential_id == "cred-1"
        assert summary.provider == "local"
        assert summary.provider_display_name == "Email & Password"
        assert summary.provider_user_id == "alice@example.com"
        assert summary.is_removable is False

    def test_is_frozen(self) -> None:
        summary = CredentialSummary(
            credential_id="cred-1",
            provider="local",
            provider_display_name="Email & Password",
            provider_user_id="alice@example.com",
            is_removable=False,
        )
        with pytest.raises(AttributeError):
            summary.provider = "google"  # type: ignore[misc]


class TestUserListCredentialSummaries:
    """User.list_credential_summaries() returns CredentialSummary VOs."""

    def _make_user_with_local(self) -> User:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        cred = Credential(
            credential_id="cred-local",
            user_id="u1",
            provider="local",
            provider_user_id="alice@example.com",
            hashed_secret="hashed_pw",
        )
        user.add_credential(cred)
        return user

    def test_returns_summary_for_local_credential(self) -> None:
        user = self._make_user_with_local()
        summaries = user.list_credential_summaries()
        assert len(summaries) == 1
        s = summaries[0]
        assert s.credential_id == "cred-local"
        assert s.provider == "local"
        assert s.provider_display_name == "Email & Password"
        assert s.provider_user_id == "alice@example.com"

    def test_returns_summary_for_google_credential(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        cred = Credential(
            credential_id="cred-google",
            user_id="u1",
            provider="google",
            provider_user_id="google-sub-123",
            hashed_secret=None,
        )
        user.add_credential(cred)
        summaries = user.list_credential_summaries()
        assert len(summaries) == 1
        s = summaries[0]
        assert s.provider == "google"
        assert s.provider_display_name == "Google"
        assert s.provider_user_id == "google-sub-123"

    def test_returns_summary_for_telegram_credential(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        cred = Credential(
            credential_id="cred-tg",
            user_id="u1",
            provider="telegram",
            provider_user_id="123456789",
            hashed_secret=None,
        )
        user.add_credential(cred)
        summaries = user.list_credential_summaries()
        assert len(summaries) == 1
        s = summaries[0]
        assert s.provider == "telegram"
        assert s.provider_display_name == "Telegram"
        assert s.provider_user_id == "123456789"

    def test_returns_summaries_for_multiple_providers(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        local_cred = Credential(
            credential_id="cred-local",
            user_id="u1",
            provider="local",
            provider_user_id="alice@example.com",
            hashed_secret="hashed_pw",
        )
        google_cred = Credential(
            credential_id="cred-google",
            user_id="u1",
            provider="google",
            provider_user_id="google-sub-123",
            hashed_secret=None,
        )
        telegram_cred = Credential(
            credential_id="cred-tg",
            user_id="u1",
            provider="telegram",
            provider_user_id="987654321",
            hashed_secret=None,
        )
        user.add_credential(local_cred)
        user.add_credential(google_cred)
        user.add_credential(telegram_cred)

        summaries = user.list_credential_summaries()
        assert len(summaries) == 3
        providers = {s.provider for s in summaries}
        assert providers == {"local", "google", "telegram"}

    def test_returns_empty_list_when_no_credentials(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        summaries = user.list_credential_summaries()
        assert summaries == []

    def test_unknown_provider_uses_titlecase_display_name(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        cred = Credential(
            credential_id="cred-gh",
            user_id="u1",
            provider="github",
            provider_user_id="gh-user-42",
            hashed_secret=None,
        )
        user.add_credential(cred)
        summaries = user.list_credential_summaries()
        assert summaries[0].provider_display_name == "Github"


class TestUserCanRemoveCredential:
    """User.can_remove_credential() checks business rules for removal."""

    def test_cannot_remove_sole_credential(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        cred = Credential(
            credential_id="cred-local",
            user_id="u1",
            provider="local",
            provider_user_id="alice@example.com",
            hashed_secret="hashed_pw",
        )
        user.add_credential(cred)
        assert user.can_remove_credential("local") is False

    def test_can_remove_when_multiple_credentials(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        local_cred = Credential(
            credential_id="cred-local",
            user_id="u1",
            provider="local",
            provider_user_id="alice@example.com",
            hashed_secret="hashed_pw",
        )
        google_cred = Credential(
            credential_id="cred-google",
            user_id="u1",
            provider="google",
            provider_user_id="google-sub-123",
            hashed_secret=None,
        )
        user.add_credential(local_cred)
        user.add_credential(google_cred)
        assert user.can_remove_credential("google") is True
        assert user.can_remove_credential("local") is True

    def test_cannot_remove_nonexistent_provider(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        cred = Credential(
            credential_id="cred-local",
            user_id="u1",
            provider="local",
            provider_user_id="alice@example.com",
            hashed_secret="hashed_pw",
        )
        user.add_credential(cred)
        assert user.can_remove_credential("github") is False

    def test_cannot_remove_from_empty_credentials(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        assert user.can_remove_credential("local") is False


class TestUserIsRemovableInSummary:
    """is_removable in CredentialSummary reflects can_remove_credential rules."""

    def test_sole_credential_is_not_removable(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        cred = Credential(
            credential_id="cred-local",
            user_id="u1",
            provider="local",
            provider_user_id="alice@example.com",
            hashed_secret="hashed_pw",
        )
        user.add_credential(cred)
        summaries = user.list_credential_summaries()
        assert summaries[0].is_removable is False

    def test_credentials_are_removable_when_multiple(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        local_cred = Credential(
            credential_id="cred-local",
            user_id="u1",
            provider="local",
            provider_user_id="alice@example.com",
            hashed_secret="hashed_pw",
        )
        google_cred = Credential(
            credential_id="cred-google",
            user_id="u1",
            provider="google",
            provider_user_id="google-sub-123",
            hashed_secret=None,
        )
        user.add_credential(local_cred)
        user.add_credential(google_cred)
        summaries = user.list_credential_summaries()
        removable = {s.provider: s.is_removable for s in summaries}
        assert removable["local"] is True
        assert removable["google"] is True
