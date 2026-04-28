"""Tests for CreateUserInviteCodeUseCase."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from auth.application.create_user_invite_code import CreateUserInviteCodeUseCase
from tests.auth.fakes.fake_unit_of_work import FakeUnitOfWork


class TestCreateUserInviteCodeUseCase:
    def test_returns_invite_code(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateUserInviteCodeUseCase(uow)

        invite = use_case.execute(user_id="user-1")

        assert invite is not None
        assert len(invite.code) == 8

    def test_issued_by_and_inviter_id_are_set_to_user(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateUserInviteCodeUseCase(uow)

        invite = use_case.execute(user_id="user-42")

        assert invite.issued_by == "user-42"
        assert invite.inviter_id == "user-42"

    def test_code_is_single_use_by_default(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateUserInviteCodeUseCase(uow)

        invite = use_case.execute(user_id="user-1")

        assert invite.max_uses == 1
        assert invite.uses_left == 1

    def test_code_expires_in_7_days_by_default(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateUserInviteCodeUseCase(uow)
        before = datetime.now(timezone.utc)

        invite = use_case.execute(user_id="user-1")

        assert invite.expires_at is not None
        delta = invite.expires_at - before
        assert 6 <= delta.days <= 7

    def test_code_is_active_on_creation(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateUserInviteCodeUseCase(uow)

        invite = use_case.execute(user_id="user-1")

        assert invite.is_active is True

    def test_code_is_persisted(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateUserInviteCodeUseCase(uow)

        invite = use_case.execute(user_id="user-1")

        found = uow.invite_codes.find_by_code(invite.code)
        assert found is not None
        assert found.code_id == invite.code_id

    def test_commits_transaction(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateUserInviteCodeUseCase(uow)

        use_case.execute(user_id="user-1")

        assert uow.committed is True

    def test_raises_when_user_id_is_empty(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateUserInviteCodeUseCase(uow)

        with pytest.raises(ValueError, match="user_id cannot be empty"):
            use_case.execute(user_id="")

    def test_raises_when_max_uses_is_zero(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateUserInviteCodeUseCase(uow)

        with pytest.raises(ValueError, match="max_uses must be at least 1"):
            use_case.execute(user_id="user-1", max_uses=0)

    def test_raises_when_expires_days_is_zero(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateUserInviteCodeUseCase(uow)

        with pytest.raises(ValueError, match="expires_days must be at least 1"):
            use_case.execute(user_id="user-1", expires_days=0)

    def test_custom_expires_days(self) -> None:
        uow = FakeUnitOfWork()
        use_case = CreateUserInviteCodeUseCase(uow)
        before = datetime.now(timezone.utc)

        invite = use_case.execute(user_id="user-1", expires_days=30)

        assert invite.expires_at is not None
        delta = invite.expires_at - before
        assert 29 <= delta.days <= 30
