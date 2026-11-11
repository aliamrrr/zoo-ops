"""Level 01: cache-aside on Redis for slow, expensive answers (LLM calls, embeddings).

Cache-aside read path:
    1. look the key up in Redis
    2. hit  -> deserialize and return it
    3. miss -> call the loader (the slow source of truth), store the result with a TTL, return it

Values are stored as JSON so any client (Python, Node, redis-cli) can read them.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence
from typing import Any, TypeVar

from redis import Redis

T = TypeVar("T")


class CacheAside:
    def __init__(self, redis: Redis, namespace: str, default_ttl: int) -> None:
        if default_ttl <= 0:
            raise ValueError("default_ttl must be positive: an entry without TTL never heals")
        self._redis = redis
        self._namespace = namespace
        self._default_ttl = default_ttl

    def redis_key(self, key: str) -> str:
        return f"{self._namespace}:{key}"

    def get_or_load(self, key: str, loader: Callable[[], T], ttl: int | None = None) -> T:
        """Return the cached value for `key`, calling `loader` only on a miss.

        Contract:
        - the Redis key is `self.redis_key(key)`
        - a hit never calls `loader`, even when the cached value is falsy (0, "", [], None)
        - a miss stores `json.dumps(value)` with `ttl` seconds, or the default TTL
        - if `loader` raises, nothing is written and the exception propagates
        """
        # TODO(level 01): implement the cache-aside read path.
        raise NotImplementedError("CacheAside.get_or_load")

    def invalidate(self, key: str) -> None:
        """Drop `key` so the next read goes back to the source of truth."""
        # TODO(level 01): one Redis command is enough.
        raise NotImplementedError("CacheAside.invalidate")


def llm_cache_key(model: str, messages: Sequence[dict[str, Any]], temperature: float) -> str | None:
    """Build a deterministic cache key for an LLM call, or None when it must not be cached.

    Contract:
    - temperature > 0 means sampled output: return None (caching would freeze one random answer)
    - same model and same messages give the same key, whatever the key order inside each dict
    - format: "llm:<model>:<sha256 hex digest of the canonical JSON of messages>"
      canonical JSON = json.dumps(..., sort_keys=True, separators=(",", ":"))
    """
    # TODO(level 01): canonical JSON, then sha256.
    raise NotImplementedError("llm_cache_key")


def embedding_key(model: str, text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"emb:{model}:{digest}"


def embed_many(
    redis: Redis,
    model: str,
    texts: Sequence[str],
    embed_batch: Callable[[list[str]], list[list[float]]],
    ttl: int,
) -> list[list[float]]:
    """Return one embedding per text, paying the provider only for texts not cached yet.

    Contract:
    - the cache key of a text is `embedding_key(model, text)`
    - read every key in one round trip (MGET)
    - call `embed_batch` at most once, with the missing texts only, in their original order,
      and not at all when everything is cached
    - store the new vectors as JSON with `ttl` and return vectors aligned with `texts`
    """
    # TODO(level 01): batch read, batch compute, batch write.
    raise NotImplementedError("embed_many")
