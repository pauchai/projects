"""Unit tests for User.update_profile() domain method."""

import pytest

from auth.domain.user import User


def make_user(
    user_id: str = "u1",
    email: str = "original@example.com",
    display_name: str = "Original Name",
) -> User:
    return User(user_id=user_id, email=email, display_name=display_name)


class TestUpdateProfileEmail:
    def test_update_email_changes_stored_email(self) -> None:
        user = make_user()
        user.update_profile(email="new@example.com")
        assert user.email == "new@example.com"

    def test_update_email_normalizes_to_lowercase(self) -> None:
        user = make_user()
        user.update_profile(email="NEW@EXAMPLE.COM")
        assert user.email == "new@example.com"

    def test_update_email_strips_whitespace(self) -> None:
        user = make_user()
        user.update_profile(email="  spaced@example.com  ")
        assert user.email == "spaced@example.com"

    def test_update_email_rejects_empty_string(self) -> None:
        user = make_user()
        with pytest.raises(ValueError, match="Email cannot be empty"):
            user.update_profile(email="   ")

    def test_update_email_rejects_missing_at_sign(self) -> None:
        user = make_user()
        with pytest.raises(ValueError, match="Invalid email format"):
            user.update_profile(email="notanemail")

    def test_update_email_none_leaves_email_unchanged(self) -> None:
        user = make_user(email="original@example.com")
        user.update_profile(email=None)
        assert user.email == "original@example.com"


class TestUpdateProfileDisplayName:
    def test_update_display_name_changes_stored_name(self) -> None:
        user = make_user()
        user.update_profile(display_name="New Name")
        assert user.display_name == "New Name"

    def test_update_display_name_strips_whitespace(self) -> None:
        user = make_user()
        user.update_profile(display_name="  Trimmed  ")
        assert user.display_name == "Trimmed"

    def test_update_display_name_rejects_empty_string(self) -> None:
        user = make_user()
        with pytest.raises(ValueError, match="Display name cannot be empty"):
            user.update_profile(display_name="   ")

    def test_update_display_name_rejects_too_long(self) -> None:
        user = make_user()
        with pytest.raises(
            ValueError, match="Display name cannot exceed 100 characters"
        ):
            user.update_profile(display_name="x" * 101)

    def test_update_display_name_accepts_exactly_100_chars(self) -> None:
        user = make_user()
        user.update_profile(display_name="x" * 100)
        assert len(user.display_name) == 100

    def test_update_display_name_none_leaves_name_unchanged(self) -> None:
        user = make_user(display_name="Original Name")
        user.update_profile(display_name=None)
        assert user.display_name == "Original Name"


class TestUpdateProfileBothFields:
    def test_update_both_fields_simultaneously(self) -> None:
        user = make_user()
        user.update_profile(email="both@example.com", display_name="Both Updated")
        assert user.email == "both@example.com"
        assert user.display_name == "Both Updated"

    def test_update_neither_field_is_noop(self) -> None:
        user = make_user(email="original@example.com", display_name="Original")
        user.update_profile()
        assert user.email == "original@example.com"
        assert user.display_name == "Original"

    def test_synthetic_telegram_email_can_be_replaced(self) -> None:
        """Key scenario: Telegram user sets a real email."""
        user = make_user(email="123456789@telegram.user", display_name="Telegram User")
        user.update_profile(email="real@example.com")
        assert user.email == "real@example.com"
