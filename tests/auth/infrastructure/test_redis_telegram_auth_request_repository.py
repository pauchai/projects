"""Unit tests for RedisTelegramAuthRequestRepository.

Uses fakeredis to test repository logic without a real Redis instance.
Follows TDD: these tests were written BEFORE the implementation.
"""

import time

import pytest

from auth.domain.telegram_auth_request import TelegramAuthRequest

# fakeredis is optional — skip tests if not installed
fakeredis = pytest.importorskip("fakeredis")

from auth.infrastructure.redis_telegram_auth_request_repository import (
    RedisTelegramAuthRequestRepository,
)


@pytest.fixture()
def fake_redis():
    """Create a fakeredis client for testing."""
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture()
def repo(fake_redis):
    """Create a repository with a short TTL for testing."""
    return RedisTelegramAuthRequestRepository(fake_redis, ttl_seconds=300)


# ---------------------------------------------------------------------------
# save + find_by_auth_code
# ---------------------------------------------------------------------------


class TestFindByAuthCode:
    def test_save_and_find_by_auth_code(
        self, repo: RedisTelegramAuthRequestRepository
    ) -> None:
        """A saved request can be found by its auth_code."""
        request = TelegramAuthRequest(auth_code="abc123", state="state-xyz")
        repo.save(request)

        found = repo.find_by_auth_code("abc123")

        assert found is not None
        assert found.auth_code == "abc123"
        assert found.state == "state-xyz"
        assert found.is_used is False
        assert found.authorization_code is None
        assert found.telegram_user_id is None

    def test_find_by_auth_code_returns_none_for_missing(
        self, repo: RedisTelegramAuthRequestRepository
    ) -> None:
        """Returns None when auth_code does not exist."""
        assert repo.find_by_auth_code("nonexistent") is None

    def test_find_by_auth_code_preserves_filled_telegram_data(
        self, repo: RedisTelegramAuthRequestRepository
    ) -> None:
        """After fill_telegram_data + save, all fields are preserved on reload."""
        request = TelegramAuthRequest(auth_code="abc123", state="state-xyz")
        request.fill_telegram_data(
            telegram_user_id="tg-999",
            telegram_username="john_doe",
            telegram_first_name="John",
            authorization_code="authz-456",
        )
        repo.save(request)

        found = repo.find_by_auth_code("abc123")

        assert found is not None
        assert found.telegram_user_id == "tg-999"
        assert found.telegram_username == "john_doe"
        assert found.telegram_first_name == "John"
        assert found.authorization_code == "authz-456"
        assert found.is_used is False

    def test_find_by_auth_code_preserves_consumed_state(
        self, repo: RedisTelegramAuthRequestRepository
    ) -> None:
        """After consume() + save, is_used flag is preserved on reload."""
        request = TelegramAuthRequest(auth_code="abc123", state="state-xyz")
        request.fill_telegram_data(
            telegram_user_id="tg-999",
            telegram_username="john_doe",
            telegram_first_name="John",
            authorization_code="authz-456",
        )
        request.consume()
        repo.save(request)

        found = repo.find_by_auth_code("abc123")

        assert found is not None
        assert found.is_used is True

    def test_find_by_auth_code_preserves_none_username(
        self, repo: RedisTelegramAuthRequestRepository
    ) -> None:
        """telegram_username=None is preserved correctly (not stored as string 'None')."""
        request = TelegramAuthRequest(auth_code="abc123", state="state-xyz")
        request.fill_telegram_data(
            telegram_user_id="tg-999",
            telegram_username=None,
            telegram_first_name="John",
            authorization_code="authz-456",
        )
        repo.save(request)

        found = repo.find_by_auth_code("abc123")

        assert found is not None
        assert found.telegram_username is None


# ---------------------------------------------------------------------------
# find_by_authorization_code (secondary index)
# ---------------------------------------------------------------------------


class TestFindByAuthorizationCode:
    def test_find_by_authorization_code(
        self, repo: RedisTelegramAuthRequestRepository
    ) -> None:
        """A saved request with authorization_code can be found by that code."""
        request = TelegramAuthRequest(auth_code="abc123", state="state-xyz")
        request.fill_telegram_data(
            telegram_user_id="tg-999",
            telegram_username="john_doe",
            telegram_first_name="John",
            authorization_code="authz-456",
        )
        repo.save(request)

        found = repo.find_by_authorization_code("authz-456")

        assert found is not None
        assert found.auth_code == "abc123"
        assert found.authorization_code == "authz-456"

    def test_find_by_authorization_code_returns_none_for_missing(
        self, repo: RedisTelegramAuthRequestRepository
    ) -> None:
        """Returns None when authorization_code does not exist."""
        assert repo.find_by_authorization_code("nonexistent") is None

    def test_find_by_authorization_code_returns_none_before_fill(
        self, repo: RedisTelegramAuthRequestRepository
    ) -> None:
        """Before fill_telegram_data, there is no authorization_code to find."""
        request = TelegramAuthRequest(auth_code="abc123", state="state-xyz")
        repo.save(request)

        assert repo.find_by_authorization_code("anything") is None


# ---------------------------------------------------------------------------
# save overwrites (update semantics)
# ---------------------------------------------------------------------------


class TestSaveOverwrites:
    def test_save_updates_existing_record(
        self, repo: RedisTelegramAuthRequestRepository
    ) -> None:
        """Saving the same auth_code twice updates the record, not duplicates it."""
        request = TelegramAuthRequest(auth_code="abc123", state="state-xyz")
        repo.save(request)

        # Fill and save again
        request.fill_telegram_data(
            telegram_user_id="tg-999",
            telegram_username="john_doe",
            telegram_first_name="John",
            authorization_code="authz-456",
        )
        repo.save(request)

        found = repo.find_by_auth_code("abc123")
        assert found is not None
        assert found.telegram_user_id == "tg-999"
        assert found.authorization_code == "authz-456"

        # Also findable by authorization_code
        found_by_authz = repo.find_by_authorization_code("authz-456")
        assert found_by_authz is not None
        assert found_by_authz.auth_code == "abc123"


# ---------------------------------------------------------------------------
# TTL behavior
# ---------------------------------------------------------------------------


class TestTtlExpiration:
    def test_record_expires_after_ttl(self, fake_redis) -> None:
        """Records should disappear after TTL expires."""
        repo = RedisTelegramAuthRequestRepository(fake_redis, ttl_seconds=1)

        request = TelegramAuthRequest(auth_code="abc123", state="state-xyz")
        request.fill_telegram_data(
            telegram_user_id="tg-999",
            telegram_username="john_doe",
            telegram_first_name="John",
            authorization_code="authz-456",
        )
        repo.save(request)

        # Immediately findable
        assert repo.find_by_auth_code("abc123") is not None
        assert repo.find_by_authorization_code("authz-456") is not None

        # Wait for TTL to expire
        time.sleep(1.5)

        # Both primary and secondary index should be gone
        assert repo.find_by_auth_code("abc123") is None
        assert repo.find_by_authorization_code("authz-456") is None

    def test_keys_have_ttl_set(self, fake_redis) -> None:
        """Verify that Redis keys have a TTL set on them."""
        repo = RedisTelegramAuthRequestRepository(fake_redis, ttl_seconds=300)

        request = TelegramAuthRequest(auth_code="abc123", state="state-xyz")
        request.fill_telegram_data(
            telegram_user_id="tg-999",
            telegram_username=None,
            telegram_first_name="John",
            authorization_code="authz-456",
        )
        repo.save(request)

        primary_ttl = fake_redis.ttl("telegram_auth:abc123")
        index_ttl = fake_redis.ttl("telegram_auth_by_authz:authz-456")

        assert 0 < primary_ttl <= 300
        assert 0 < index_ttl <= 300


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestDelete:
    def test_delete_removes_record_and_index(
        self, repo: RedisTelegramAuthRequestRepository
    ) -> None:
        """delete() removes both primary key and secondary index."""
        request = TelegramAuthRequest(auth_code="abc123", state="state-xyz")
        request.fill_telegram_data(
            telegram_user_id="tg-999",
            telegram_username="john_doe",
            telegram_first_name="John",
            authorization_code="authz-456",
        )
        repo.save(request)

        repo.delete("abc123")

        assert repo.find_by_auth_code("abc123") is None
        assert repo.find_by_authorization_code("authz-456") is None

    def test_delete_nonexistent_does_not_raise(
        self, repo: RedisTelegramAuthRequestRepository
    ) -> None:
        """Deleting a nonexistent record is a no-op."""
        repo.delete("nonexistent")  # should not raise
