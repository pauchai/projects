"""Redis-based TelegramAuthRequestRepository (driven adapter).

Replaces the SQLAlchemy-based repository with Redis storage that provides
automatic TTL-based expiration.  This eliminates the accumulation problem
where ``telegram_auth_requests`` records grew indefinitely in PostgreSQL.

Key design:
- Primary storage: ``telegram_auth:{auth_code}`` → Redis Hash with all fields.
- Secondary index: ``telegram_auth_by_authz:{authorization_code}`` → String
  containing the ``auth_code`` (for reverse lookup).
- Both keys share the same TTL so they expire together.
- ``None`` values are stored as a sentinel (empty string) and restored on read.

Implements the ``TelegramAuthRequestRepository`` Protocol defined in
``auth.domain.ports``.
"""

from __future__ import annotations

from datetime import datetime, timezone

from redis import Redis

from auth.domain.telegram_auth_request import TelegramAuthRequest

# Key prefixes
_PRIMARY_PREFIX = "telegram_auth:"
_INDEX_PREFIX = "telegram_auth_by_authz:"

# Sentinel for None values in Redis (Redis cannot store None)
_NONE_SENTINEL = ""

# Default TTL: 5 minutes
DEFAULT_TTL_SECONDS = 300


class RedisTelegramAuthRequestRepository:
    """Implements TelegramAuthRequestRepository Protocol using Redis.

    Each ``TelegramAuthRequest`` is stored as a Redis Hash with automatic
    TTL-based expiration.  A secondary index key maps
    ``authorization_code → auth_code`` for reverse lookups.
    """

    def __init__(
        self, redis_client: Redis, ttl_seconds: int = DEFAULT_TTL_SECONDS
    ) -> None:
        self._redis = redis_client
        self._ttl_seconds = ttl_seconds

    # ------------------------------------------------------------------
    # Public interface (matches TelegramAuthRequestRepository Protocol)
    # ------------------------------------------------------------------

    def find_by_auth_code(self, auth_code: str) -> TelegramAuthRequest | None:
        """Find an auth request by its auth_code (primary key)."""
        key = f"{_PRIMARY_PREFIX}{auth_code}"
        data = self._redis.hgetall(key)
        if not data:
            return None
        return self._deserialize(data)

    def find_by_authorization_code(
        self, authorization_code: str
    ) -> TelegramAuthRequest | None:
        """Find an auth request by the authorization_code (secondary index)."""
        index_key = f"{_INDEX_PREFIX}{authorization_code}"
        auth_code = self._redis.get(index_key)
        if auth_code is None:
            return None
        return self.find_by_auth_code(auth_code)

    def save(self, request: TelegramAuthRequest) -> None:
        """Persist a TelegramAuthRequest with automatic TTL expiration."""
        key = f"{_PRIMARY_PREFIX}{request.auth_code}"
        data = self._serialize(request)

        pipe = self._redis.pipeline()
        pipe.hset(key, mapping=data)
        pipe.expire(key, self._ttl_seconds)

        # Create/update secondary index if authorization_code is set
        if request.authorization_code is not None:
            index_key = f"{_INDEX_PREFIX}{request.authorization_code}"
            pipe.set(index_key, request.auth_code)
            pipe.expire(index_key, self._ttl_seconds)

        pipe.execute()

    def delete(self, auth_code: str) -> None:
        """Remove a TelegramAuthRequest and its secondary index."""
        key = f"{_PRIMARY_PREFIX}{auth_code}"

        # Read authorization_code before deleting so we can clean up the index
        authorization_code = self._redis.hget(key, "authorization_code")

        pipe = self._redis.pipeline()
        pipe.delete(key)
        if authorization_code and authorization_code != _NONE_SENTINEL:
            index_key = f"{_INDEX_PREFIX}{authorization_code}"
            pipe.delete(index_key)
        pipe.execute()

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize(request: TelegramAuthRequest) -> dict[str, str]:
        """Convert a TelegramAuthRequest to a flat dict for Redis HSET."""
        return {
            "auth_code": request.auth_code,
            "state": request.state,
            "authorization_code": request.authorization_code or _NONE_SENTINEL,
            "telegram_user_id": request.telegram_user_id or _NONE_SENTINEL,
            "telegram_username": request.telegram_username or _NONE_SENTINEL,
            "telegram_first_name": request.telegram_first_name or _NONE_SENTINEL,
            "is_used": "1" if request.is_used else "0",
            "created_at": request.created_at.isoformat(),
        }

    @staticmethod
    def _deserialize(data: dict[str, str]) -> TelegramAuthRequest:
        """Reconstruct a TelegramAuthRequest from a Redis Hash dict.

        Bypasses ``__init__`` validation (same approach as SQLAlchemy ORM
        imperative mapping — the data is already validated on creation).
        """
        request = object.__new__(TelegramAuthRequest)
        request.auth_code = data["auth_code"]
        request.state = data["state"]
        request.authorization_code = data["authorization_code"] or None
        if request.authorization_code == _NONE_SENTINEL:
            request.authorization_code = None
        request.telegram_user_id = data.get("telegram_user_id") or None
        if request.telegram_user_id == _NONE_SENTINEL:
            request.telegram_user_id = None
        request.telegram_username = data.get("telegram_username") or None
        if request.telegram_username == _NONE_SENTINEL:
            request.telegram_username = None
        request.telegram_first_name = data.get("telegram_first_name") or None
        if request.telegram_first_name == _NONE_SENTINEL:
            request.telegram_first_name = None
        request.is_used = data.get("is_used") == "1"
        request.created_at = datetime.fromisoformat(data["created_at"])
        return request
