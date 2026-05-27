import pytest
from datetime import datetime, timedelta, timezone

from community.domain.invite_code import CommunityInviteCode


class TestCommunityInviteCodeInit:
    def test_creates_valid_code(self) -> None:
        code = CommunityInviteCode(
            code_id="c1", code="ABC123", community_id="comm-1", issued_by="user-1"
        )
        assert code.code_id == "c1"
        assert code.code == "ABC123"
        assert code.community_id == "comm-1"
        assert code.issued_by == "user-1"
        assert code.max_uses == 1
        assert code.uses_left == 1
        assert code.is_active is True
        assert code.role == "member"

    def test_normalizes_code_to_upper(self) -> None:
        code = CommunityInviteCode(
            code_id="c1", code="abc123", community_id="comm-1", issued_by="user-1"
        )
        assert code.code == "ABC123"

    def test_strips_code_whitespace(self) -> None:
        code = CommunityInviteCode(
            code_id="c1", code="  abc  ", community_id="comm-1", issued_by="user-1"
        )
        assert code.code == "ABC"

    def test_rejects_empty_code(self) -> None:
        with pytest.raises(ValueError, match="Code cannot be empty"):
            CommunityInviteCode(
                code_id="c1", code="  ", community_id="comm-1", issued_by="user-1"
            )

    def test_rejects_max_uses_below_one(self) -> None:
        with pytest.raises(ValueError, match="max_uses must be at least 1"):
            CommunityInviteCode(
                code_id="c1", code="ABC", community_id="comm-1",
                issued_by="user-1", max_uses=0,
            )

    def test_rejects_empty_community_id(self) -> None:
        with pytest.raises(ValueError, match="community_id is required"):
            CommunityInviteCode(
                code_id="c1", code="ABC", community_id="", issued_by="user-1"
            )

    def test_accepts_custom_role(self) -> None:
        code = CommunityInviteCode(
            code_id="c1", code="ABC", community_id="comm-1",
            issued_by="user-1", role="admin",
        )
        assert code.role == "admin"

    def test_sets_expires_at(self) -> None:
        future = datetime.now(timezone.utc) + timedelta(days=7)
        code = CommunityInviteCode(
            code_id="c1", code="ABC", community_id="comm-1",
            issued_by="user-1", expires_at=future,
        )
        assert code.expires_at == future


class TestCommunityInviteCodeIsValid:
    def test_returns_true_for_valid_code(self) -> None:
        code = CommunityInviteCode(
            code_id="c1", code="ABC", community_id="comm-1", issued_by="user-1"
        )
        assert code.is_valid() is True

    def test_returns_false_when_inactive(self) -> None:
        code = CommunityInviteCode(
            code_id="c1", code="ABC", community_id="comm-1", issued_by="user-1"
        )
        code.deactivate()
        assert code.is_valid() is False

    def test_returns_false_when_uses_exhausted(self) -> None:
        code = CommunityInviteCode(
            code_id="c1", code="ABC", community_id="comm-1", issued_by="user-1",
            max_uses=1,
        )
        code.redeem()
        assert code.is_valid() is False

    def test_returns_false_when_expired(self) -> None:
        expired = datetime.now(timezone.utc) - timedelta(hours=1)
        code = CommunityInviteCode(
            code_id="c1", code="ABC", community_id="comm-1",
            issued_by="user-1", expires_at=expired,
        )
        assert code.is_valid() is False

    def test_uses_custom_now(self) -> None:
        future = datetime.now(timezone.utc) + timedelta(days=7)
        code = CommunityInviteCode(
            code_id="c1", code="ABC", community_id="comm-1",
            issued_by="user-1", expires_at=future,
        )
        assert code.is_valid(now=future - timedelta(days=1)) is True
        assert code.is_valid(now=future + timedelta(days=1)) is False

    def test_no_expiry_never_expires(self) -> None:
        code = CommunityInviteCode(
            code_id="c1", code="ABC", community_id="comm-1", issued_by="user-1",
            expires_at=None,
        )
        assert code.is_valid() is True

    def test_still_valid_with_remaining_uses(self) -> None:
        code = CommunityInviteCode(
            code_id="c1", code="ABC", community_id="comm-1",
            issued_by="user-1", max_uses=5,
        )
        code.redeem()
        code.redeem()
        assert code.uses_left == 3
        assert code.is_valid() is True


class TestCommunityInviteCodeRedeem:
    def test_decrements_uses_left(self) -> None:
        code = CommunityInviteCode(
            code_id="c1", code="ABC", community_id="comm-1",
            issued_by="user-1", max_uses=3,
        )
        code.redeem()
        assert code.uses_left == 2
        code.redeem()
        assert code.uses_left == 1

    def test_raises_when_inactive(self) -> None:
        code = CommunityInviteCode(
            code_id="c1", code="ABC", community_id="comm-1", issued_by="user-1"
        )
        code.deactivate()
        with pytest.raises(ValueError, match="no longer active"):
            code.redeem()

    def test_raises_when_fully_used(self) -> None:
        code = CommunityInviteCode(
            code_id="c1", code="ABC", community_id="comm-1", issued_by="user-1",
            max_uses=1,
        )
        code.redeem()
        with pytest.raises(ValueError, match="already been fully used"):
            code.redeem()

    def test_raises_when_expired(self) -> None:
        expired = datetime.now(timezone.utc) - timedelta(hours=1)
        code = CommunityInviteCode(
            code_id="c1", code="ABC", community_id="comm-1",
            issued_by="user-1", expires_at=expired,
        )
        with pytest.raises(ValueError, match="expired"):
            code.redeem()


class TestCommunityInviteCodeDeactivate:
    def test_sets_inactive(self) -> None:
        code = CommunityInviteCode(
            code_id="c1", code="ABC", community_id="comm-1", issued_by="user-1"
        )
        code.deactivate()
        assert code.is_active is False

    def test_raises_if_already_inactive(self) -> None:
        code = CommunityInviteCode(
            code_id="c1", code="ABC", community_id="comm-1", issued_by="user-1"
        )
        code.deactivate()
        with pytest.raises(ValueError, match="already inactive"):
            code.deactivate()
