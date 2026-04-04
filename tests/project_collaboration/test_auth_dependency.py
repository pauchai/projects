"""Unit tests for the _extract_user_id auth dependency logic.

Tests the JWT Bearer token extraction and validation logic in isolation,
using a fake TokenService.
"""

from __future__ import annotations

import pytest

from project_collaboration.api.dependencies import (
    AuthenticationError,
    _extract_user_id,
)


class FakeTokenService:
    """Fake: decodes tokens of the form 'fake-token:{user_id}'."""

    def create_access_token(self, user_id: str) -> str:
        return f"fake-token:{user_id}"

    def decode_token(self, token: str) -> str:
        if not token.startswith("fake-token:"):
            raise ValueError("Invalid token")
        return token[len("fake-token:") :]


class TestExtractUserId:
    def test_extracts_user_id_from_valid_bearer_token(self) -> None:
        token_service = FakeTokenService()
        user_id = _extract_user_id(
            authorization="Bearer fake-token:user-123",
            token_service=token_service,
        )
        assert user_id == "user-123"

    def test_raises_authentication_error_when_no_header(self) -> None:
        token_service = FakeTokenService()
        with pytest.raises(AuthenticationError, match="Missing"):
            _extract_user_id(
                authorization=None,
                token_service=token_service,
            )

    def test_raises_authentication_error_when_not_bearer(self) -> None:
        token_service = FakeTokenService()
        with pytest.raises(AuthenticationError, match="Bearer"):
            _extract_user_id(
                authorization="Basic abc123",
                token_service=token_service,
            )

    def test_raises_authentication_error_when_token_invalid(self) -> None:
        token_service = FakeTokenService()
        with pytest.raises(AuthenticationError, match="Invalid"):
            _extract_user_id(
                authorization="Bearer bad-token-here",
                token_service=token_service,
            )

    def test_raises_authentication_error_when_bearer_has_no_token(self) -> None:
        token_service = FakeTokenService()
        with pytest.raises(AuthenticationError, match="Missing"):
            _extract_user_id(
                authorization="Bearer ",
                token_service=token_service,
            )
