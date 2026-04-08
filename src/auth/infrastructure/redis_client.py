"""Redis connection factory for the Auth bounded context.

Provides a module-level Redis client configured via the ``REDIS_URL``
environment variable.  Used by ``RedisTelegramAuthRequestRepository``.
"""

import os

from redis import Redis

DEFAULT_REDIS_URL = "redis://localhost:6379/0"


def get_redis_client(url: str | None = None) -> Redis:
    """Create a Redis client from a URL or ``REDIS_URL`` env var.

    Args:
        url: Explicit Redis URL.  Falls back to the ``REDIS_URL``
            environment variable, then to ``DEFAULT_REDIS_URL``.

    Returns:
        A connected ``redis.Redis`` instance with ``decode_responses=True``.
    """
    redis_url = url or os.environ.get("REDIS_URL", DEFAULT_REDIS_URL)
    return Redis.from_url(redis_url, decode_responses=True)
