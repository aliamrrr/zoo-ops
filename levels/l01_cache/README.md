# 01 Cache: The Nut Store

**In the game.** Visitors ask the Owl (a slow, expensive LLM) the same six questions over and over. Hazel the squirrel keeps answers in her nut store (Redis) so the Owl only thinks once per question.

## The pattern

- **Cache-aside**: the app reads the cache first, and on a miss loads from the source of truth and fills the cache. The cache never talks to the database itself.
- **TTL**: every entry expires. A bug or a stale value heals by itself.
- **Invalidation**: when the source of truth changes, delete the key. The next read refills it.
- **LLM cache**: only deterministic calls (temperature 0) are cacheable, keyed by a hash of the canonical prompt.
- **Embedding cache**: embeddings never change for a given model and text. Batch read, compute only the missing ones, batch write.

## What you write

In [cache.py](cache.py): `CacheAside.get_or_load`, `CacheAside.invalidate`, `llm_cache_key`, `embed_many`.

## How it breaks in the game

| Bug | What you see |
| --- | --- |
| No caching | The Owl answers 30 times for 6 questions, the bill and latency explode |
| No invalidation | The lion fact changed but visitors still get the old answer |
| Non canonical prompt key | Two identical prompts never share a cache entry |
| Caching sampled output | Every visitor gets the exact same "random" poem |
| Per-text embedding calls | The provider is paid for texts already cached |

## Learn it

- [Caching patterns (AWS whitepaper)](https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/caching-patterns.html)
- [Redis SET command, EX option](https://redis.io/docs/latest/commands/set/) and [MGET](https://redis.io/docs/latest/commands/mget/)
- [redis-py pipelines](https://redis.readthedocs.io/en/stable/advanced_features.html#default-pipelines)

## Hints

- `redis.get` returns `None` on a miss, and bytes on a hit. Test `is None`, not truthiness.
- `json.dumps(..., sort_keys=True, separators=(",", ":"))` gives one canonical string per value.
- `zip(missing_indexes, vectors, strict=True)` keeps the batch aligned.

```
python -m zoo test 1
python -m zoo scene 1
```
