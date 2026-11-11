"""Scene 01: visitors keep asking the Owl the same questions."""

from __future__ import annotations

import fakeredis

from levels.l01_cache.cache import CacheAside, embed_many, llm_cache_key
from zoo.kit import Scene

OWL_LATENCY_MS = 800
CACHE_LATENCY_MS = 1
OWL_COST_EUR = 0.02


class SlowOwl:
    def __init__(self) -> None:
        self.facts = {
            "lion": "Lions sleep up to 20 hours a day.",
            "zebra": "No two zebras share the same stripes.",
            "otter": "Sea otters hold hands while they sleep.",
            "flamingo": "Flamingos are pink because of what they eat.",
            "owl": "Owls cannot move their eyes, so they turn their heads.",
            "sloth": "Sloths can hold their breath for 40 minutes.",
        }
        self.calls = 0

    def answer(self, topic: str) -> str:
        self.calls += 1
        return self.facts[topic]


def play(scene: Scene) -> None:
    owl = SlowOwl()
    cache = CacheAside(fakeredis.FakeRedis(), "owl", default_ttl=300)
    questions = list(owl.facts) * 5

    latency_ms = 0
    for topic in questions:
        before = owl.calls
        cache.get_or_load(topic, lambda topic=topic: owl.answer(topic))
        latency_ms += OWL_LATENCY_MS if owl.calls > before else CACHE_LATENCY_MS

    scene.info(f"{len(questions)} visitors ask {len(owl.facts)} different questions.")
    scene.metric("owl calls", owl.calls)
    scene.metric("owl bill", f"{owl.calls * OWL_COST_EUR:.2f} EUR")
    scene.metric("avg latency", f"{latency_ms / len(questions):.0f} ms")
    scene.check(
        owl.calls == len(owl.facts),
        "Hazel answers repeats from the nut store: the Owl only thinks once per question.",
        f"The Owl answered {owl.calls} times for {len(owl.facts)} questions. "
        "The bill and the queue explode.",
    )

    owl.facts["lion"] = "Lions now follow a strict vegetable diet (keeper's orders)."
    cache.invalidate("lion")
    fresh = cache.get_or_load("lion", lambda: owl.answer("lion"))
    scene.check(
        fresh == owl.facts["lion"],
        "The lion fact changed, the entry was invalidated, visitors get the new answer.",
        "The lion fact changed but the nut store still serves the stale answer.",
    )

    question = [{"role": "user", "content": "What do otters eat?"}]
    reordered = [{"content": "What do otters eat?", "role": "user"}]
    key = llm_cache_key("owl-large", question, temperature=0.0)
    scene.check(
        key is not None and key == llm_cache_key("owl-large", reordered, temperature=0.0),
        "Same prompt, same LLM cache key, even with JSON keys in another order.",
        "Two identical prompts produced different LLM cache keys: the cache never hits.",
    )
    scene.check(
        llm_cache_key("owl-large", [{"role": "user", "content": "A poem"}], 0.9) is None,
        "Creative poems (temperature 0.9) are never frozen in cache.",
        "A sampled poem was cached: every visitor now gets the exact same 'random' poem.",
    )

    paid: list[str] = []

    def embed_batch(texts: list[str]) -> list[list[float]]:
        paid.extend(texts)
        return [[float(len(text))] for text in texts]

    redis = fakeredis.FakeRedis()
    embed_many(redis, "emb-1", ["lion", "zebra"], embed_batch, ttl=3600)
    embed_many(redis, "emb-1", ["lion", "zebra", "otter"], embed_batch, ttl=3600)
    scene.metric("embeddings paid", len(paid))
    scene.check(
        paid == ["lion", "zebra", "otter"],
        "Embeddings: only the new text 'otter' was sent to the provider.",
        f"Embeddings paid for {paid}, expected each text exactly once.",
    )
