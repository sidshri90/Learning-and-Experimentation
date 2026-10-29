import asyncio
from collections.abc import Awaitable, Callable
from collections.abc import Hashable
from typing import Any

from cachetools import TTLCache


class AsyncTTLCache:
    """TTL cache for async work.

    Concurrent requests for the same missing key share one upstream call.
    Failures are never cached, so the next request retries.
    """

    def __init__(self, maxsize: int, ttl: float) -> None:
        self._data: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._locks: dict[Hashable, asyncio.Lock] = {}

    async def get_or_set(self, key: Hashable, factory: Callable[[], Awaitable[Any]]) -> Any:
        try:
            return self._data[key]
        except KeyError:
            pass
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            try:
                return self._data[key]  # another waiter may have filled it
            except KeyError:
                pass
            try:
                value = await factory()
            finally:
                self._locks.pop(key, None)
            self._data[key] = value
            return value
