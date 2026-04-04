"""Tests for JwtTokenService — infrastructure adapter."""

import time

import pytest

from auth.infrastructure.jwt_token_service import JwtTokenService


class TestJwtTokenService:
    """JwtTokenService wraps PyJWT for the TokenService port."""

    def test_create_and_decode_round_trip(self) -> None:
        service = JwtTokenService(secret="test-secret", algorithm="HS256")
        token = service.create_access_token("user-42")
        decoded_user_id = service.decode_token(token)
        assert decoded_user_id == "user-42"

    def test_decode_returns_correct_user_id(self) -> None:
        service = JwtTokenService(secret="test-secret", algorithm="HS256")
        token = service.create_access_token("abc-123")
        assert service.decode_token(token) == "abc-123"

    def test_decode_raises_on_invalid_token(self) -> None:
        service = JwtTokenService(secret="test-secret", algorithm="HS256")
        with pytest.raises(ValueError, match="Invalid token"):
            service.decode_token("not-a-real-jwt")

    def test_decode_raises_on_wrong_secret(self) -> None:
        service_a = JwtTokenService(secret="secret-a", algorithm="HS256")
        service_b = JwtTokenService(secret="secret-b", algorithm="HS256")
        token = service_a.create_access_token("user-1")
        with pytest.raises(ValueError, match="Invalid token"):
            service_b.decode_token(token)

    def test_decode_raises_on_expired_token(self) -> None:
        service = JwtTokenService(
            secret="test-secret", algorithm="HS256", expire_minutes=0
        )
        # expire_minutes=0 means token expires immediately
        token = service.create_access_token("user-1")
        time.sleep(1)  # ensure it's expired
        with pytest.raises(ValueError, match="Invalid token"):
            service.decode_token(token)

    def test_token_contains_user_id_claim(self) -> None:
        service = JwtTokenService(secret="test-secret", algorithm="HS256")
        token = service.create_access_token("user-99")
        # Decode without validation to inspect claims
        import jwt

        payload = jwt.decode(
            token, "test-secret", algorithms=["HS256"], options={"verify_exp": False}
        )
        assert payload["sub"] == "user-99"
