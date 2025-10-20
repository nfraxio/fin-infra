from __future__ import annotations

from cashews import cache
from loguru import logger


def init_cache(redis_url: str | None) -> None:
    if redis_url:
        cache.setup(redis_url)
        logger.debug("Cache configured for Redis: {}", redis_url)
    else:
        cache.setup("mem://")
        logger.debug("Cache configured for in-memory backend")


def cached(ttl: int = 60):
    def wrapper(func):
        return cache(ttl=ttl)(func)

    return wrapper
