"""Tests for User aggregate root."""

import pytest
from datetime import datetime, timezone

from auth.domain.user import User, Credential


class TestUserCreation:
    """User is created with email, display name, and active status."""

    def test_stores_identity_fields(self) -> None:
        user = User(
            user_id="u1",
            email="alice@example.com",
            display_name="Alice",
        )
        assert user.user_id == "u1"
        assert user.email == "alice@example.com"
        assert user.display_name == "Alice"

    def test_is_active_by_default(self) -> None:
        user = User(
            user_id="u1",
            email="alice@example.com",
            display_name="Alice",
        )
        assert user.is_active is True

    def test_has_created_at_timestamp(self) -> None:
        before = datetime.now(timezone.utc)
        user = User(
            user_id="u1",
            email="alice@example.com",
            display_name="Alice",
        )
        after = datetime.now(timezone.utc)
        assert before <= user.created_at <= after

    def test_starts_with_empty_credentials(self) -> None:
        user = User(
            user_id="u1",
            email="alice@example.com",
            display_name="Alice",
        )
        assert user.credentials == []


class TestUserEmailValidation:
    """Email must be valid and non-empty."""

    def test_email_cannot_be_empty(self) -> None:
        with pytest.raises(ValueError, match="Email cannot be empty"):
            User(user_id="u1", email="", display_name="Alice")

    def test_email_cannot_be_whitespace(self) -> None:
        with pytest.raises(ValueError, match="Email cannot be empty"):
            User(user_id="u1", email="   ", display_name="Alice")

    def test_email_must_contain_at_sign(self) -> None:
        with pytest.raises(ValueError, match="Invalid email format"):
            User(user_id="u1", email="alice-example.com", display_name="Alice")

    def test_email_is_normalized_to_lowercase(self) -> None:
        user = User(
            user_id="u1",
            email="Alice@Example.COM",
            display_name="Alice",
        )
        assert user.email == "alice@example.com"


class TestUserDisplayNameValidation:
    """Display name must be between 1 and 100 characters."""

    def test_display_name_cannot_be_empty(self) -> None:
        with pytest.raises(ValueError, match="Display name cannot be empty"):
            User(user_id="u1", email="alice@example.com", display_name="")

    def test_display_name_cannot_be_whitespace(self) -> None:
        with pytest.raises(ValueError, match="Display name cannot be empty"):
            User(user_id="u1", email="alice@example.com", display_name="   ")

    def test_display_name_cannot_exceed_100_chars(self) -> None:
        with pytest.raises(
            ValueError, match="Display name cannot exceed 100 characters"
        ):
            User(
                user_id="u1",
                email="alice@example.com",
                display_name="A" * 101,
            )

    def test_display_name_is_stripped(self) -> None:
        user = User(
            user_id="u1",
            email="alice@example.com",
            display_name="  Alice  ",
        )
        assert user.display_name == "Alice"


class TestUserCredentialManagement:
    """User manages credentials for different auth providers."""

    def test_add_credential(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        cred = Credential(
            credential_id="cred-1",
            user_id="u1",
            provider="local",
            provider_user_id="alice@example.com",
            hashed_secret="hashed_pw",
        )
        user.add_credential(cred)
        assert len(user.credentials) == 1
        assert user.credentials[0] is cred

    def test_add_duplicate_provider_raises(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        cred1 = Credential(
            credential_id="cred-1",
            user_id="u1",
            provider="local",
            provider_user_id="alice@example.com",
            hashed_secret="hashed_pw",
        )
        cred2 = Credential(
            credential_id="cred-2",
            user_id="u1",
            provider="local",
            provider_user_id="alice@example.com",
            hashed_secret="other_hash",
        )
        user.add_credential(cred1)
        with pytest.raises(ValueError, match="already has a credential for provider"):
            user.add_credential(cred2)

    def test_find_credential_by_provider(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        cred = Credential(
            credential_id="cred-1",
            user_id="u1",
            provider="local",
            provider_user_id="alice@example.com",
            hashed_secret="hashed_pw",
        )
        user.add_credential(cred)
        found = user.find_credential_by_provider("local")
        assert found is cred

    def test_find_credential_by_provider_returns_none_when_missing(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        assert user.find_credential_by_provider("google") is None

    def test_has_credential_for_provider(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        cred = Credential(
            credential_id="cred-1",
            user_id="u1",
            provider="local",
            provider_user_id="alice@example.com",
            hashed_secret="hashed_pw",
        )
        user.add_credential(cred)
        assert user.has_credential_for_provider("local") is True
        assert user.has_credential_for_provider("google") is False

    def test_add_multiple_providers(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        local_cred = Credential(
            credential_id="cred-1",
            user_id="u1",
            provider="local",
            provider_user_id="alice@example.com",
            hashed_secret="hashed_pw",
        )
        google_cred = Credential(
            credential_id="cred-2",
            user_id="u1",
            provider="google",
            provider_user_id="google-sub-123",
            hashed_secret=None,
        )
        user.add_credential(local_cred)
        user.add_credential(google_cred)
        assert len(user.credentials) == 2
        assert user.has_credential_for_provider("local") is True
        assert user.has_credential_for_provider("google") is True


class TestUserDeactivation:
    """User can be deactivated and reactivated."""

    def test_deactivate_user(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        user.deactivate()
        assert user.is_active is False

    def test_deactivate_already_inactive_raises(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        user.deactivate()
        with pytest.raises(ValueError, match="User is already inactive"):
            user.deactivate()

    def test_reactivate_user(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        user.deactivate()
        user.reactivate()
        assert user.is_active is True

    def test_reactivate_already_active_raises(self) -> None:
        user = User(user_id="u1", email="alice@example.com", display_name="Alice")
        with pytest.raises(ValueError, match="User is already active"):
            user.reactivate()
