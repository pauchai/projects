"""Tests for the InviteCode domain entity."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from auth.domain.invite_code import InviteCode


def _make_code(
    *,
    code: str = "ABCD1234",
    max_uses: int = 1,
    expires_at: datetime | None = None,
) -> InviteCode:
    return InviteCode(
        code_id="cid-1",
        code=code,
        issued_by="admin-1",
        max_uses=max_uses,
        expires_at=expires_at,
    )


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestInviteCodeConstruction:
    def test_stores_code_uppercased_and_stripped(self) -> None:
        invite = InviteCode(code_id="x", code="  abcd1234  ", issued_by="admin")
        assert invite.code == "ABCD1234"

    def test_raises_when_code_is_blank(self) -> None:
        with pytest.raises(ValueError, match="Code cannot be empty"):
            InviteCode(code_id="x", code="   ", issued_by="admin")

    def test_raises_when_max_uses_is_zero(self) -> None:
        with pytest.raises(ValueError, match="max_uses must be at least 1"):
            InviteCode(code_id="x", code="ABCD1234", issued_by="admin", max_uses=0)

    def test_raises_when_max_uses_is_negative(self) -> None:
        with pytest.raises(ValueError, match="max_uses must be at least 1"):
            InviteCode(code_id="x", code="ABCD1234", issued_by="admin", max_uses=-1)

    def test_is_active_on_creation(self) -> None:
        invite = _make_code()
        assert invite.is_active is True

    def test_uses_left_equals_max_uses_on_creation(self) -> None:
        invite = _make_code(max_uses=3)
        assert invite.uses_left == 3

    def test_inviter_id_defaults_to_none(self) -> None:
        invite = _make_code()
        assert invite.inviter_id is None

    def test_inviter_id_can_be_set(self) -> None:
        invite = InviteCode(
            code_id="x", code="ABCD1234", issued_by="admin", inviter_id="user-99"
        )
        assert invite.inviter_id == "user-99"


# ---------------------------------------------------------------------------
# is_valid
# ---------------------------------------------------------------------------


class TestInviteCodeIsValid:
    def test_fresh_code_is_valid(self) -> None:
        assert _make_code().is_valid() is True

    def test_inactive_code_is_not_valid(self) -> None:
        invite = _make_code()
        invite.is_active = False
        assert invite.is_valid() is False

    def test_exhausted_code_is_not_valid(self) -> None:
        invite = _make_code(max_uses=1)
        invite.uses_left = 0
        assert invite.is_valid() is False

    def test_expired_code_is_not_valid(self) -> None:
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        invite = _make_code(expires_at=past)
        assert invite.is_valid() is False

    def test_not_yet_expired_code_is_valid(self) -> None:
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        invite = _make_code(expires_at=future)
        assert invite.is_valid() is True

    def test_is_valid_with_injected_now(self) -> None:
        """is_valid accepts explicit `now` for deterministic tests."""
        expiry = datetime(2030, 1, 1, tzinfo=timezone.utc)
        invite = _make_code(expires_at=expiry)
        before = datetime(2029, 12, 31, tzinfo=timezone.utc)
        after = datetime(2030, 1, 2, tzinfo=timezone.utc)
        assert invite.is_valid(now=before) is True
        assert invite.is_valid(now=after) is False


# ---------------------------------------------------------------------------
# redeem
# ---------------------------------------------------------------------------


class TestInviteCodeRedeem:
    def test_redeem_decrements_uses_left(self) -> None:
        invite = _make_code(max_uses=2)
        invite.redeem()
        assert invite.uses_left == 1

    def test_redeem_twice_exhausts_multi_use_code(self) -> None:
        invite = _make_code(max_uses=2)
        invite.redeem()
        invite.redeem()
        assert invite.uses_left == 0

    def test_redeem_raises_when_inactive(self) -> None:
        invite = _make_code()
        invite.is_active = False
        with pytest.raises(ValueError, match="no longer active"):
            invite.redeem()

    def test_redeem_raises_when_exhausted(self) -> None:
        invite = _make_code(max_uses=1)
        invite.redeem()
        with pytest.raises(ValueError, match="fully used"):
            invite.redeem()

    def test_redeem_raises_when_expired(self) -> None:
        past = datetime.now(timezone.utc) - timedelta(seconds=1)
        invite = _make_code(expires_at=past)
        with pytest.raises(ValueError, match="expired"):
            invite.redeem()

    def test_redeem_accepts_injected_now(self) -> None:
        expiry = datetime(2030, 6, 1, tzinfo=timezone.utc)
        invite = _make_code(expires_at=expiry)
        before = datetime(2030, 5, 31, tzinfo=timezone.utc)
        invite.redeem(now=before)  # should not raise
        assert invite.uses_left == 0


# ---------------------------------------------------------------------------
# deactivate
# ---------------------------------------------------------------------------


class TestInviteCodeDeactivate:
    def test_deactivate_sets_is_active_to_false(self) -> None:
        invite = _make_code()
        invite.deactivate()
        assert invite.is_active is False

    def test_deactivate_makes_code_invalid(self) -> None:
        invite = _make_code()
        invite.deactivate()
        assert invite.is_valid() is False

    def test_deactivate_raises_when_already_inactive(self) -> None:
        invite = _make_code()
        invite.deactivate()
        with pytest.raises(ValueError, match="already inactive"):
            invite.deactivate()
