"""Tests for Credential entity."""

import pytest
from datetime import datetime, timezone

from auth.domain.user import Credential


class TestCredentialCreation:
    """Credential stores provider identity and optional secret."""

    def test_stores_identity_fields(self) -> None:
        cred = Credential(
            credential_id="cred-1",
            user_id="u1",
            provider="local",
            provider_user_id="user@example.com",
            hashed_secret="hashed_pw_123",
        )
        assert cred.credential_id == "cred-1"
        assert cred.user_id == "u1"
        assert cred.provider == "local"
        assert cred.provider_user_id == "user@example.com"
        assert cred.hashed_secret == "hashed_pw_123"

    def test_local_credential_requires_hashed_secret(self) -> None:
        with pytest.raises(
            ValueError, match="Local credentials require a hashed secret"
        ):
            Credential(
                credential_id="cred-1",
                user_id="u1",
                provider="local",
                provider_user_id="user@example.com",
                hashed_secret=None,
            )

    def test_oauth_credential_allows_none_secret(self) -> None:
        cred = Credential(
            credential_id="cred-1",
            user_id="u1",
            provider="google",
            provider_user_id="google-sub-123",
            hashed_secret=None,
        )
        assert cred.hashed_secret is None

    def test_has_created_at_timestamp(self) -> None:
        before = datetime.now(timezone.utc)
        cred = Credential(
            credential_id="cred-1",
            user_id="u1",
            provider="local",
            provider_user_id="user@example.com",
            hashed_secret="hashed",
        )
        after = datetime.now(timezone.utc)
        assert before <= cred.created_at <= after

    def test_provider_cannot_be_empty(self) -> None:
        with pytest.raises(ValueError, match="Provider cannot be empty"):
            Credential(
                credential_id="cred-1",
                user_id="u1",
                provider="",
                provider_user_id="user@example.com",
                hashed_secret="hashed",
            )

    def test_provider_user_id_cannot_be_empty(self) -> None:
        with pytest.raises(ValueError, match="Provider user ID cannot be empty"):
            Credential(
                credential_id="cred-1",
                user_id="u1",
                provider="local",
                provider_user_id="",
                hashed_secret="hashed",
            )
