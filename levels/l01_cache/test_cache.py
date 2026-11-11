import json

import fakeredis
import pytest

from levels.l01_cache.cache import CacheAside, embed_many, embedding_key, llm_cache_key


class CountingLoader:
    def __init__(self, value: object) -> None:
        self.value = value
        self.calls = 0

    def __call__(self) -> object:
        self.calls += 1
        return self.value


@pytest.fixture
def redis() -> fakeredis.FakeRedis:
    return fakeredis.FakeRedis()


@pytest.fixture
def cache(redis: fakeredis.FakeRedis) -> CacheAside:
    return CacheAside(redis, "owl", default_ttl=60)


def test_miss_then_hit_calls_loader_once(cache: CacheAside) -> None:
    loader = CountingLoader({"answer": "Lions sleep 20 hours a day"})
    first = cache.get_or_load("lion", loader)
    second = cache.get_or_load("lion", loader)
    assert first == second == loader.value
    assert loader.calls == 1, "a hit must not call the loader"


def test_value_is_json_under_namespaced_key(cache: CacheAside, redis: fakeredis.FakeRedis) -> None:
    cache.get_or_load("lion", CountingLoader({"answer": "meat"}))
    raw = redis.get("owl:lion")
    assert raw is not None, "expected the value under the key 'owl:lion'"
    assert json.loads(raw) == {"answer": "meat"}


def test_entry_gets_the_default_ttl(cache: CacheAside, redis: fakeredis.FakeRedis) -> None:
    cache.get_or_load("lion", CountingLoader("meat"))
    assert 0 < redis.ttl("owl:lion") <= 60, "every cache entry needs a TTL"


def test_explicit_ttl_overrides_the_default(cache: CacheAside, redis: fakeredis.FakeRedis) -> None:
    cache.get_or_load("lion", CountingLoader("meat"), ttl=5)
    assert 0 < redis.ttl("owl:lion") <= 5


@pytest.mark.parametrize("falsy", [0, "", [], None, False])
def test_falsy_values_are_still_hits(cache: CacheAside, falsy: object) -> None:
    loader = CountingLoader(falsy)
    cache.get_or_load("empty", loader)
    assert cache.get_or_load("empty", loader) == falsy
    assert loader.calls == 1, "testing the decoded value (`if value:`) turns falsy hits to misses"


def test_loader_failure_is_not_cached(cache: CacheAside, redis: fakeredis.FakeRedis) -> None:
    def broken() -> str:
        raise TimeoutError("owl asleep")

    with pytest.raises(TimeoutError):
        cache.get_or_load("lion", broken)
    assert redis.get("owl:lion") is None


def test_invalidate_forces_a_reload(cache: CacheAside) -> None:
    loader = CountingLoader("meat")
    cache.get_or_load("lion", loader)
    cache.invalidate("lion")
    cache.get_or_load("lion", loader)
    assert loader.calls == 2


def test_llm_key_ignores_dict_key_order() -> None:
    a = llm_cache_key("owl-large", [{"role": "user", "content": "hi"}], 0.0)
    b = llm_cache_key("owl-large", [{"content": "hi", "role": "user"}], 0.0)
    assert a is not None and a == b
    assert a.startswith("llm:owl-large:")


def test_llm_key_changes_with_model_or_prompt() -> None:
    messages = [{"role": "user", "content": "hi"}]
    base = llm_cache_key("owl-large", messages, 0.0)
    assert base != llm_cache_key("owl-small", messages, 0.0)
    assert base != llm_cache_key("owl-large", [{"role": "user", "content": "hello"}], 0.0)


def test_sampled_calls_are_not_cached() -> None:
    assert llm_cache_key("owl-large", [{"role": "user", "content": "a poem"}], 0.9) is None


def test_embed_many_only_pays_for_missing_texts(redis: fakeredis.FakeRedis) -> None:
    redis.set(embedding_key("emb-1", "lion"), json.dumps([1.0, 0.0]))
    batches: list[list[str]] = []

    def embed_batch(texts: list[str]) -> list[list[float]]:
        batches.append(texts)
        return [[float(len(text)), 1.0] for text in texts]

    vectors = embed_many(redis, "emb-1", ["tiger", "lion", "zebra"], embed_batch, ttl=3600)

    assert batches == [["tiger", "zebra"]], "one provider call, missing texts only, in order"
    assert vectors == [[5.0, 1.0], [1.0, 0.0], [5.0, 1.0]]
    assert 0 < redis.ttl(embedding_key("emb-1", "tiger")) <= 3600


def test_embed_many_skips_the_provider_when_all_cached(redis: fakeredis.FakeRedis) -> None:
    redis.set(embedding_key("emb-1", "lion"), json.dumps([1.0]))

    def embed_batch(texts: list[str]) -> list[list[float]]:
        raise AssertionError("the provider must not be called when everything is cached")

    assert embed_many(redis, "emb-1", ["lion"], embed_batch, ttl=60) == [[1.0]]
