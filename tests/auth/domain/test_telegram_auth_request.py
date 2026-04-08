"""Unit tests for TelegramAuthRequest domain entity."""

import pytest

from auth.domain.telegram_auth_request import TelegramAuthRequest


class TestTelegramAuthRequestCreation:
    """Tests for TelegramAuthRequest.__init__."""

    def test_creates_with_valid_auth_code_and_state(self) -> None:
        req = TelegramAuthRequest(auth_code="abc123", state="xyz789")
        assert req.auth_code == "abc123"
        assert req.state == "xyz789"

    def test_initial_state_is_not_ready(self) -> None:
        req = TelegramAuthRequest(auth_code="abc123", state="xyz789")
        assert req.is_ready is False
        assert req.is_used is False
        assert req.authorization_code is None
        assert req.telegram_user_id is None

    def test_raises_when_auth_code_is_empty(self) -> None:
        with pytest.raises(ValueError, match="auth_code cannot be empty"):
            TelegramAuthRequest(auth_code="", state="xyz789")

    def test_raises_when_auth_code_is_whitespace(self) -> None:
        with pytest.raises(ValueError, match="auth_code cannot be empty"):
            TelegramAuthRequest(auth_code="   ", state="xyz789")

    def test_raises_when_state_is_empty(self) -> None:
        with pytest.raises(ValueError, match="state cannot be empty"):
            TelegramAuthRequest(auth_code="abc123", state="")


class TestFillTelegramData:
    """Tests for TelegramAuthRequest.fill_telegram_data."""

    def test_fills_telegram_data_successfully(self) -> None:
        req = TelegramAuthRequest(auth_code="abc123", state="xyz789")
        req.fill_telegram_data(
            telegram_user_id="12345",
            telegram_username="john_doe",
            telegram_first_name="John",
            authorization_code="auth-code-xyz",
        )
        assert req.telegram_user_id == "12345"
        assert req.telegram_username == "john_doe"
        assert req.telegram_first_name == "John"
        assert req.authorization_code == "auth-code-xyz"

    def test_is_ready_after_filling_data(self) -> None:
        req = TelegramAuthRequest(auth_code="abc123", state="xyz789")
        req.fill_telegram_data(
            telegram_user_id="12345",
            telegram_username=None,
            telegram_first_name="John",
            authorization_code="auth-code-xyz",
        )
        assert req.is_ready is True

    def test_allows_none_username(self) -> None:
        req = TelegramAuthRequest(auth_code="abc123", state="xyz789")
        req.fill_telegram_data(
            telegram_user_id="12345",
            telegram_username=None,
            telegram_first_name="John",
            authorization_code="auth-code-xyz",
        )
        assert req.telegram_username is None

    def test_raises_when_already_filled(self) -> None:
        req = TelegramAuthRequest(auth_code="abc123", state="xyz789")
        req.fill_telegram_data(
            telegram_user_id="12345",
            telegram_username="john",
            telegram_first_name="John",
            authorization_code="auth-code-1",
        )
        with pytest.raises(ValueError, match="already been filled"):
            req.fill_telegram_data(
                telegram_user_id="67890",
                telegram_username="jane",
                telegram_first_name="Jane",
                authorization_code="auth-code-2",
            )

    def test_raises_when_already_used(self) -> None:
        req = TelegramAuthRequest(auth_code="abc123", state="xyz789")
        req.fill_telegram_data(
            telegram_user_id="12345",
            telegram_username="john",
            telegram_first_name="John",
            authorization_code="auth-code-1",
        )
        req.consume()
        with pytest.raises(ValueError, match="already been used"):
            req.fill_telegram_data(
                telegram_user_id="67890",
                telegram_username="jane",
                telegram_first_name="Jane",
                authorization_code="auth-code-2",
            )

    def test_raises_when_telegram_user_id_empty(self) -> None:
        req = TelegramAuthRequest(auth_code="abc123", state="xyz789")
        with pytest.raises(ValueError, match="telegram_user_id cannot be empty"):
            req.fill_telegram_data(
                telegram_user_id="",
                telegram_username="john",
                telegram_first_name="John",
                authorization_code="auth-code-1",
            )

    def test_raises_when_first_name_empty(self) -> None:
        req = TelegramAuthRequest(auth_code="abc123", state="xyz789")
        with pytest.raises(ValueError, match="telegram_first_name cannot be empty"):
            req.fill_telegram_data(
                telegram_user_id="12345",
                telegram_username="john",
                telegram_first_name="",
                authorization_code="auth-code-1",
            )

    def test_raises_when_authorization_code_empty(self) -> None:
        req = TelegramAuthRequest(auth_code="abc123", state="xyz789")
        with pytest.raises(ValueError, match="authorization_code cannot be empty"):
            req.fill_telegram_data(
                telegram_user_id="12345",
                telegram_username="john",
                telegram_first_name="John",
                authorization_code="",
            )


class TestConsume:
    """Tests for TelegramAuthRequest.consume."""

    def test_consume_marks_as_used(self) -> None:
        req = TelegramAuthRequest(auth_code="abc123", state="xyz789")
        req.fill_telegram_data(
            telegram_user_id="12345",
            telegram_username="john",
            telegram_first_name="John",
            authorization_code="auth-code-1",
        )
        req.consume()
        assert req.is_used is True
        assert req.is_ready is False

    def test_consume_raises_when_not_ready(self) -> None:
        req = TelegramAuthRequest(auth_code="abc123", state="xyz789")
        with pytest.raises(ValueError, match="not been completed by the bot"):
            req.consume()

    def test_consume_raises_when_already_used(self) -> None:
        req = TelegramAuthRequest(auth_code="abc123", state="xyz789")
        req.fill_telegram_data(
            telegram_user_id="12345",
            telegram_username="john",
            telegram_first_name="John",
            authorization_code="auth-code-1",
        )
        req.consume()
        with pytest.raises(ValueError, match="already been used"):
            req.consume()
