"""Tests for UpdateProfileUseCase — TDD.

Scenarios:
1. Happy path: update email only.
2. Happy path: update display_name only.
3. Happy path: update both fields simultaneously.
4. Happy path: sending the user's own email does not raise (self-update).
5. Happy path: no-op when both fields are None.
6. Happy path: transaction is committed on success.
7. Error: user not found → LookupError.
8. Error: email taken by another user → ValueError.
9. Error: transaction is NOT committed on error.
"""

import pytest

from auth.application.update_profile import UpdateProfileUseCase
from auth.domain.user import User
from tests.auth.fakes.fake_unit_of_work import FakeUnitOfWork


def _make_user(
    user_id: str = "u1",
    email: str = "alice@example.com",
    display_name: str = "Alice",
) -> User:
    return User(user_id=user_id, email=email, display_name=display_name)


class TestUpdateProfileHappyPath:
    def test_update_email_changes_user_email(self) -> None:
        uow = FakeUnitOfWork()
        uow.users.save(_make_user(user_id="u1", email="old@example.com"))

        use_case = UpdateProfileUseCase(uow)
        result = use_case.execute("u1", email="new@example.com")

        assert result.email == "new@example.com"
        assert uow.users.find_by_id("u1").email == "new@example.com"

    def test_update_display_name_changes_display_name(self) -> None:
        uow = FakeUnitOfWork()
        uow.users.save(_make_user(user_id="u1", display_name="Old Name"))

        use_case = UpdateProfileUseCase(uow)
        result = use_case.execute("u1", display_name="New Name")

        assert result.display_name == "New Name"
        assert uow.users.find_by_id("u1").display_name == "New Name"

    def test_update_both_fields(self) -> None:
        uow = FakeUnitOfWork()
        uow.users.save(_make_user(user_id="u1"))

        use_case = UpdateProfileUseCase(uow)
        result = use_case.execute("u1", email="both@example.com", display_name="Both")

        assert result.email == "both@example.com"
        assert result.display_name == "Both"

    def test_sending_own_email_does_not_raise(self) -> None:
        """User PATCHes with their existing email — should be a no-op, not a conflict."""
        uow = FakeUnitOfWork()
        uow.users.save(_make_user(user_id="u1", email="alice@example.com"))

        use_case = UpdateProfileUseCase(uow)
        result = use_case.execute("u1", email="alice@example.com")

        assert result.email == "alice@example.com"

    def test_noop_when_both_fields_none(self) -> None:
        uow = FakeUnitOfWork()
        uow.users.save(
            _make_user(user_id="u1", email="alice@example.com", display_name="Alice")
        )

        use_case = UpdateProfileUseCase(uow)
        result = use_case.execute("u1")

        assert result.email == "alice@example.com"
        assert result.display_name == "Alice"

    def test_commits_transaction(self) -> None:
        uow = FakeUnitOfWork()
        uow.users.save(_make_user(user_id="u1"))

        use_case = UpdateProfileUseCase(uow)
        use_case.execute("u1", display_name="Committed")

        assert uow.committed is True

    def test_returns_updated_profile_dataclass(self) -> None:
        uow = FakeUnitOfWork()
        uow.users.save(
            _make_user(user_id="u1", email="old@example.com", display_name="Old")
        )

        use_case = UpdateProfileUseCase(uow)
        result = use_case.execute("u1", email="ret@example.com", display_name="Ret")

        assert result.user_id == "u1"
        assert result.email == "ret@example.com"
        assert result.display_name == "Ret"

    def test_synthetic_telegram_email_can_be_replaced(self) -> None:
        """Key scenario: Telegram user updates to a real email."""
        uow = FakeUnitOfWork()
        uow.users.save(_make_user(user_id="u1", email="123456789@telegram.user"))

        use_case = UpdateProfileUseCase(uow)
        result = use_case.execute("u1", email="real@example.com")

        assert result.email == "real@example.com"


class TestUpdateProfileErrorCases:
    def test_raises_lookup_error_when_user_not_found(self) -> None:
        uow = FakeUnitOfWork()

        use_case = UpdateProfileUseCase(uow)
        with pytest.raises(LookupError, match="User nonexistent not found"):
            use_case.execute("nonexistent", email="x@example.com")

    def test_raises_value_error_when_email_taken_by_another_user(self) -> None:
        uow = FakeUnitOfWork()
        uow.users.save(_make_user(user_id="u1", email="alice@example.com"))
        uow.users.save(_make_user(user_id="u2", email="bob@example.com"))

        use_case = UpdateProfileUseCase(uow)
        with pytest.raises(ValueError, match="Email already registered"):
            use_case.execute("u1", email="bob@example.com")

    def test_does_not_commit_on_lookup_error(self) -> None:
        uow = FakeUnitOfWork()

        use_case = UpdateProfileUseCase(uow)
        with pytest.raises(LookupError):
            use_case.execute("nonexistent")

        assert uow.committed is False

    def test_does_not_commit_on_email_conflict(self) -> None:
        uow = FakeUnitOfWork()
        uow.users.save(_make_user(user_id="u1", email="alice@example.com"))
        uow.users.save(_make_user(user_id="u2", email="bob@example.com"))

        use_case = UpdateProfileUseCase(uow)
        with pytest.raises(ValueError):
            use_case.execute("u1", email="bob@example.com")

        assert uow.committed is False
