"""Unit tests for TelegramOAuthClient adapter."""

import pytest

from auth.domain.oauth import OAuthError
from auth.domain.telegram_auth_request import TelegramAuthRequest
from auth.infrastructure.providers.telegram_oauth_client import TelegramOAuthClient


def _make_ready_request() -> TelegramAuthRequest:
    """Create a TelegramAuthRequest with telegram data filled in."""
    req = TelegramAuthRequest(auth_code="abc123", state="xyz789")
    req.fill_telegram_data(
        telegram_user_id="12345",
        telegram_username="john_doe",
        telegram_first_name="John",
        authorization_code="auth-code-xyz",
    )
    return req


class TestBuildAuthorizationUrl:
    """Tests for TelegramOAuthClient.build_authorization_url."""

    def test_returns_telegram_deep_link(self) -> None:
        client = TelegramOAuthClient(bot_username="test_bot")
        url = client.build_authorization_url("my-auth-code")
        assert url == "https://t.me/test_bot?start=my-auth-code"

    def test_includes_bot_username(self) -> None:
        client = TelegramOAuthClient(bot_username="another_bot")
        url = client.build_authorization_url("code123")
        assert "another_bot" in url

    def test_includes_auth_code_as_start_param(self) -> None:
        client = TelegramOAuthClient(bot_username="test_bot")
        url = client.build_authorization_url("my-special-code")
        assert url.endswith("?start=my-special-code")


class TestExchangeCode:
    """Tests for TelegramOAuthClient.exchange_code."""

    def test_returns_code_when_request_is_ready(self) -> None:
        client = TelegramOAuthClient(bot_username="test_bot")
        req = _make_ready_request()
        client.set_auth_request(req)

        result = client.exchange_code("auth-code-xyz")
        assert result == "auth-code-xyz"

    def test_raises_when_no_auth_request_set(self) -> None:
        client = TelegramOAuthClient(bot_username="test_bot")
        with pytest.raises(OAuthError, match="No Telegram auth request found"):
            client.exchange_code("some-code")

    def test_raises_when_code_mismatch_for_unfilled_request(self) -> None:
        client = TelegramOAuthClient(bot_username="test_bot")
        req = TelegramAuthRequest(auth_code="abc", state="xyz")
        client.set_auth_request(req)

        with pytest.raises(OAuthError, match="Authorization code mismatch"):
            client.exchange_code("some-code")

    def test_raises_when_code_mismatch(self) -> None:
        client = TelegramOAuthClient(bot_username="test_bot")
        req = _make_ready_request()
        client.set_auth_request(req)

        with pytest.raises(OAuthError, match="Authorization code mismatch"):
            client.exchange_code("wrong-code")


class TestGetUserInfo:
    """Tests for TelegramOAuthClient.get_user_info."""

    def test_returns_oauth_user_info(self) -> None:
        client = TelegramOAuthClient(bot_username="test_bot")
        req = _make_ready_request()
        client.set_auth_request(req)

        info = client.get_user_info("auth-code-xyz")

        assert info.provider == "telegram"
        assert info.provider_user_id == "12345"
        assert info.email == "12345@telegram.user"

    def test_uses_username_as_display_name_when_available(self) -> None:
        client = TelegramOAuthClient(bot_username="test_bot")
        req = _make_ready_request()
        client.set_auth_request(req)

        info = client.get_user_info("auth-code-xyz")
        assert info.display_name == "john_doe"

    def test_uses_first_name_when_no_username(self) -> None:
        client = TelegramOAuthClient(bot_username="test_bot")
        req = TelegramAuthRequest(auth_code="abc", state="xyz")
        req.fill_telegram_data(
            telegram_user_id="12345",
            telegram_username=None,
            telegram_first_name="John",
            authorization_code="auth-code-xyz",
        )
        client.set_auth_request(req)

        info = client.get_user_info("auth-code-xyz")
        assert info.display_name == "John"

    def test_generates_synthetic_email(self) -> None:
        client = TelegramOAuthClient(bot_username="test_bot")
        req = _make_ready_request()
        client.set_auth_request(req)

        info = client.get_user_info("auth-code-xyz")
        assert info.email == "12345@telegram.user"

    def test_raises_when_no_request_set(self) -> None:
        client = TelegramOAuthClient(bot_username="test_bot")
        with pytest.raises(OAuthError, match="No Telegram user data"):
            client.get_user_info("any-token")

    def test_raises_when_request_has_no_telegram_data(self) -> None:
        client = TelegramOAuthClient(bot_username="test_bot")
        req = TelegramAuthRequest(auth_code="abc", state="xyz")
        client.set_auth_request(req)

        with pytest.raises(OAuthError, match="No Telegram user data"):
            client.get_user_info("any-token")
