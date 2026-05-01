"""Unit tests for ActivateUserWithInviteUseCase."""

from __future__ import annotations

import pytest

from auth.application.activate_user_with_invite import ActivateUserWithInviteUseCase
from auth.domain.invite_code import InviteCode
from auth.domain.user import Credential, User
from tests.auth.fakes.fake_unit_of_work import FakeTokenService, FakeUnitOfWork


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pending_user(user_id: str = "user-1", email: str = "alice@example.com") -> User:
    user = User(user_id=user_id, email=email, display_name="Alice")
    user.status = "pending"
    credential = Credential(
        credential_id="cred-1",
        user_id=user_id,
        provider="google",
        provider_user_id="google-111",
        hashed_secret=None,
    )
    user.add_credential(credential)
    return user


def _make_invite_code(
    code: str = "INVITE01",
    inviter_id: str | None = "inviter-99",
) -> InviteCode:
    return InviteCode(
        code_id="code-1",
        code=code,
        issued_by="admin",
        inviter_id=inviter_id,
        max_uses=1,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestActivateUserWithInviteUseCase:
    def test_activates_pending_user(self) -> None:
        uow = FakeUnitOfWork()
        token_service = FakeTokenService()
        user = _make_pending_user()
        uow.users.save(user)
        invite = _make_invite_code()
        uow.invite_codes.save(invite)

        use_case = ActivateUserWithInviteUseCase(uow, token_service)
        use_case.execute(user_id="user-1", invite_code="INVITE01")

        saved = uow.users.find_by_id("user-1")
        assert saved is not None
        assert saved.status == "active"

    def test_returns_token_with_active_status(self) -> None:
        uow = FakeUnitOfWork()
        token_service = FakeTokenService()
        user = _make_pending_user()
        uow.users.save(user)
        uow.invite_codes.save(_make_invite_code())

        use_case = ActivateUserWithInviteUseCase(uow, token_service)
        token = use_case.execute(user_id="user-1", invite_code="INVITE01")

        assert token == "fake-token:user-1:active"

    def test_redeems_invite_code(self) -> None:
        uow = FakeUnitOfWork()
        token_service = FakeTokenService()
        uow.users.save(_make_pending_user())
        invite = _make_invite_code(code="REDEEM01")
        uow.invite_codes.save(invite)

        use_case = ActivateUserWithInviteUseCase(uow, token_service)
        use_case.execute(user_id="user-1", invite_code="REDEEM01")

        saved_invite = uow.invite_codes.find_by_code("REDEEM01")
        assert saved_invite is not None
        assert saved_invite.uses_left == 0

    def test_sets_inviter_id_from_code(self) -> None:
        uow = FakeUnitOfWork()
        token_service = FakeTokenService()
        user = _make_pending_user()
        uow.users.save(user)
        uow.invite_codes.save(_make_invite_code(inviter_id="inviter-99"))

        use_case = ActivateUserWithInviteUseCase(uow, token_service)
        use_case.execute(user_id="user-1", invite_code="INVITE01")

        saved = uow.users.find_by_id("user-1")
        assert saved is not None
        assert saved.inviter_id == "inviter-99"

    def test_does_not_overwrite_existing_inviter_id(self) -> None:
        uow = FakeUnitOfWork()
        token_service = FakeTokenService()
        user = _make_pending_user()
        user.inviter_id = "original-inviter"
        uow.users.save(user)
        uow.invite_codes.save(_make_invite_code(inviter_id="other-inviter"))

        use_case = ActivateUserWithInviteUseCase(uow, token_service)
        use_case.execute(user_id="user-1", invite_code="INVITE01")

        saved = uow.users.find_by_id("user-1")
        assert saved is not None
        assert saved.inviter_id == "original-inviter"

    def test_commits_transaction(self) -> None:
        uow = FakeUnitOfWork()
        token_service = FakeTokenService()
        uow.users.save(_make_pending_user())
        uow.invite_codes.save(_make_invite_code())

        use_case = ActivateUserWithInviteUseCase(uow, token_service)
        use_case.execute(user_id="user-1", invite_code="INVITE01")

        assert uow.committed is True

    def test_raises_when_user_not_found(self) -> None:
        uow = FakeUnitOfWork()
        token_service = FakeTokenService()
        uow.invite_codes.save(_make_invite_code())

        use_case = ActivateUserWithInviteUseCase(uow, token_service)

        with pytest.raises(LookupError, match="not found"):
            use_case.execute(user_id="ghost-user", invite_code="INVITE01")

    def test_raises_when_user_is_inactive(self) -> None:
        uow = FakeUnitOfWork()
        token_service = FakeTokenService()
        user = _make_pending_user()
        user.deactivate()
        uow.users.save(user)
        uow.invite_codes.save(_make_invite_code())

        use_case = ActivateUserWithInviteUseCase(uow, token_service)

        with pytest.raises(ValueError, match="inactive"):
            use_case.execute(user_id="user-1", invite_code="INVITE01")

    def test_raises_when_user_already_active(self) -> None:
        uow = FakeUnitOfWork()
        token_service = FakeTokenService()
        user = _make_pending_user()
        user.status = "active"  # already active
        uow.users.save(user)
        uow.invite_codes.save(_make_invite_code())

        use_case = ActivateUserWithInviteUseCase(uow, token_service)

        with pytest.raises(ValueError, match="already active"):
            use_case.execute(user_id="user-1", invite_code="INVITE01")

    def test_raises_when_invite_code_not_found(self) -> None:
        uow = FakeUnitOfWork()
        token_service = FakeTokenService()
        uow.users.save(_make_pending_user())

        use_case = ActivateUserWithInviteUseCase(uow, token_service)

        with pytest.raises(ValueError, match="invalid or has expired"):
            use_case.execute(user_id="user-1", invite_code="NONEXISTENT")

    def test_raises_when_invite_code_exhausted(self) -> None:
        uow = FakeUnitOfWork()
        token_service = FakeTokenService()
        uow.users.save(_make_pending_user())
        exhausted_invite = InviteCode(
            code_id="code-ex",
            code="EXHAUST1",
            issued_by="admin",
            inviter_id=None,
            max_uses=1,
        )
        exhausted_invite.redeem()  # exhaust it
        uow.invite_codes.save(exhausted_invite)

        use_case = ActivateUserWithInviteUseCase(uow, token_service)

        with pytest.raises(ValueError, match="invalid or has expired"):
            use_case.execute(user_id="user-1", invite_code="EXHAUST1")

    def test_invite_code_lookup_is_case_insensitive(self) -> None:
        uow = FakeUnitOfWork()
        token_service = FakeTokenService()
        uow.users.save(_make_pending_user())
        uow.invite_codes.save(_make_invite_code(code="ABCD1234"))

        use_case = ActivateUserWithInviteUseCase(uow, token_service)
        token = use_case.execute(user_id="user-1", invite_code="abcd1234")

        assert "active" in token
