"""Tests for RegisterUserWithInviteUseCase."""

from __future__ import annotations

import pytest

from auth.application.register_user_with_invite import RegisterUserWithInviteUseCase
from auth.domain.invite_code import InviteCode
from tests.auth.fakes.fake_unit_of_work import FakePasswordHasher, FakeUnitOfWork


def _seed_invite(uow: FakeUnitOfWork, code: str = "VALIDCODE") -> InviteCode:
    """Helper: insert a valid invite code into the fake repo."""
    invite = InviteCode(code_id="cid-1", code=code, issued_by="admin-1")
    uow.invite_codes.save(invite)
    return invite


class TestRegisterUserWithInviteUseCase:
    def test_creates_user_with_given_fields(self) -> None:
        uow = FakeUnitOfWork()
        _seed_invite(uow)
        use_case = RegisterUserWithInviteUseCase(uow, FakePasswordHasher())

        use_case.execute(
            user_id="u1",
            email="alice@example.com",
            password="secret",
            display_name="Alice",
            invite_code="VALIDCODE",
        )

        user = uow.users.find_by_id("u1")
        assert user is not None
        assert user.email == "alice@example.com"
        assert user.display_name == "Alice"

    def test_hashes_password_and_attaches_local_credential(self) -> None:
        uow = FakeUnitOfWork()
        _seed_invite(uow)
        use_case = RegisterUserWithInviteUseCase(uow, FakePasswordHasher())

        use_case.execute(
            user_id="u1",
            email="alice@example.com",
            password="secret",
            display_name="Alice",
            invite_code="VALIDCODE",
        )

        user = uow.users.find_by_id("u1")
        assert user is not None
        cred = user.find_credential_by_provider("local")
        assert cred is not None
        assert cred.hashed_secret == "hashed:secret"

    def test_redeems_invite_code(self) -> None:
        uow = FakeUnitOfWork()
        invite = _seed_invite(uow)
        use_case = RegisterUserWithInviteUseCase(uow, FakePasswordHasher())

        use_case.execute(
            user_id="u1",
            email="alice@example.com",
            password="secret",
            display_name="Alice",
            invite_code="VALIDCODE",
        )

        assert invite.uses_left == 0

    def test_sets_inviter_id_from_code(self) -> None:
        uow = FakeUnitOfWork()
        invite = InviteCode(
            code_id="cid-2",
            code="REFCODE1",
            issued_by="admin-1",
            inviter_id="user-referrer",
        )
        uow.invite_codes.save(invite)
        use_case = RegisterUserWithInviteUseCase(uow, FakePasswordHasher())

        use_case.execute(
            user_id="u1",
            email="alice@example.com",
            password="secret",
            display_name="Alice",
            invite_code="REFCODE1",
        )

        user = uow.users.find_by_id("u1")
        assert user is not None
        assert user.inviter_id == "user-referrer"

    def test_inviter_id_is_none_for_admin_codes(self) -> None:
        uow = FakeUnitOfWork()
        _seed_invite(uow)
        use_case = RegisterUserWithInviteUseCase(uow, FakePasswordHasher())

        use_case.execute(
            user_id="u1",
            email="alice@example.com",
            password="secret",
            display_name="Alice",
            invite_code="VALIDCODE",
        )

        user = uow.users.find_by_id("u1")
        assert user is not None
        assert user.inviter_id is None

    def test_commits_transaction(self) -> None:
        uow = FakeUnitOfWork()
        _seed_invite(uow)
        use_case = RegisterUserWithInviteUseCase(uow, FakePasswordHasher())

        use_case.execute(
            user_id="u1",
            email="alice@example.com",
            password="secret",
            display_name="Alice",
            invite_code="VALIDCODE",
        )

        assert uow.committed is True

    def test_raises_when_invite_code_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = RegisterUserWithInviteUseCase(uow, FakePasswordHasher())

        with pytest.raises(ValueError, match="invalid or has expired"):
            use_case.execute(
                user_id="u1",
                email="alice@example.com",
                password="secret",
                display_name="Alice",
                invite_code="NONEXISTENT",
            )

    def test_raises_when_invite_code_exhausted(self) -> None:
        uow = FakeUnitOfWork()
        invite = _seed_invite(uow)
        invite.uses_left = 0  # exhaust it
        use_case = RegisterUserWithInviteUseCase(uow, FakePasswordHasher())

        with pytest.raises(ValueError, match="invalid or has expired"):
            use_case.execute(
                user_id="u1",
                email="alice@example.com",
                password="secret",
                display_name="Alice",
                invite_code="VALIDCODE",
            )

    def test_raises_when_invite_code_case_insensitive_input(self) -> None:
        """Lowercase input is normalised to uppercase before lookup."""
        uow = FakeUnitOfWork()
        _seed_invite(uow, code="VALIDCODE")
        use_case = RegisterUserWithInviteUseCase(uow, FakePasswordHasher())

        # lower-case input should still work
        use_case.execute(
            user_id="u1",
            email="alice@example.com",
            password="secret",
            display_name="Alice",
            invite_code="validcode",
        )
        user = uow.users.find_by_id("u1")
        assert user is not None

    def test_raises_when_email_already_registered(self) -> None:
        uow = FakeUnitOfWork()
        _seed_invite(uow, code="CODE0001")
        _seed_invite_extra = InviteCode(
            code_id="cid-2", code="CODE0002", issued_by="admin-1"
        )
        uow.invite_codes.save(_seed_invite_extra)
        use_case = RegisterUserWithInviteUseCase(uow, FakePasswordHasher())

        use_case.execute(
            user_id="u1",
            email="alice@example.com",
            password="secret",
            display_name="Alice",
            invite_code="CODE0001",
        )

        with pytest.raises(ValueError, match="Email already registered"):
            use_case.execute(
                user_id="u2",
                email="alice@example.com",
                password="secret",
                display_name="Alice2",
                invite_code="CODE0002",
            )
