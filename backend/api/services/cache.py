from __future__ import annotations

import time
from threading import Lock
from typing import Callable, Generic, TypeVar


T = TypeVar("T")


class SimpleTTLCache(Generic[T]):
    """A very small in-memory cache with a global TTL."""

    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = max(ttl_seconds, 0)
        self._store: dict[str, tuple[float, T]] = {}
        self._lock = Lock()

    def get_or_set(self, key: str, factory: Callable[[], T]) -> T:
        if self._ttl == 0:
            return factory()

        now = time.time()
        with self._lock:
            entry = self._store.get(key)
            if entry is not None:
                expires_at, value = entry
                if expires_at > now:
                    return value

        value = factory()
        expires_at = now + self._ttl

        with self._lock:
            self._store[key] = (expires_at, value)

        return value

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    @property
    def ttl_seconds(self) -> int:
        return self._ttl
