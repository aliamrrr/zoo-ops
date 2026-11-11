"""Live hooks of the game: the Owl kiosk and the food bowls run the learner's code on every click.

Every hook degrades gracefully: a TODO (NotImplementedError) falls back to the naive behavior,
which is exactly the behavior the pattern exists to prevent. A buggy implementation is used as
is, so its consequences show up in the game. A level file that does not even import (a typo in
the middle of an edit) only breaks its own part of the game.
"""

from __future__ import annotations

import asyncio
import functools
import importlib
import random
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any, TypeVar

import fakeredis

from zoo import owl

T = TypeVar("T")

OWL_SECONDS = 2.4
PARROT_SECONDS = 0.8
OWL_COST = 3
PARROT_COST = 1
NAIVE_TIMEOUT = 10.0
MEAL_GRAMS = 50


def level_module(name: str) -> ModuleType:
    return importlib.import_module(f"levels.{name}")


class SimClock:
    """Real time plus simulated waits: breakers see game time pass between clicks, while
    simulated provider latency and retry sleeps cost the server nothing."""

    def __init__(self) -> None:
        self._offset = 0.0

    def __call__(self) -> float:
        return time.monotonic() + self._offset

    def sleep(self, seconds: float) -> None:
        self._offset += max(0.0, seconds)


@dataclass
class AskOutcome:
    answer: str = ""
    provider: str = "none"
    cache_hit: bool = False
    cost: int = 0
    sim_seconds: float = 0.0
    failed: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass
class FeedOutcome:
    delivered_grams: int = 0
    attempts: int = 0
    replays: int = 0
    notes: list[str] = field(default_factory=list)


def add_note(notes: list[str], text: str) -> None:
    if text not in notes:
        notes.append(text)


class Kiosk:
    """The Owl, the Parrot, their breakers and the answer cache (levels 01 and 03)."""

    def __init__(self, rng: random.Random) -> None:
        self.reliability = level_module("l03_reliability.reliability")
        self.caching = level_module("l01_cache.cache")
        self.clock = SimClock()
        self.storm = False
        self.breakers = {
            "owl": self.reliability.CircuitBreaker(2, 8, self.clock),
            "parrot": self.reliability.CircuitBreaker(3, 8, self.clock),
        }
        self.policy = self.reliability.RetryPolicy(
            attempts=2, base_delay=0.3, max_delay=1.0, sleep=self.clock.sleep, rng=rng
        )
        self.cache = self.caching.CacheAside(fakeredis.FakeRedis(), "owl", default_ttl=600)
        self.providers = [
            self._provider("owl", self._owl_complete),
            self._provider("parrot", self._parrot_complete),
        ]

    @staticmethod
    def _provider(name: str, complete: Any) -> Any:
        return type(name.title(), (), {"name": name, "complete": staticmethod(complete)})()

    def _owl_complete(self, prompt: str, timeout: float) -> str:
        if self.storm:
            self.clock.sleep(timeout)
            raise self.reliability.ProviderTimeout("the bridge to the Owl is flooded")
        self.clock.sleep(min(OWL_SECONDS, timeout))
        if timeout < OWL_SECONDS:
            raise self.reliability.ProviderTimeout("timeout shorter than the Owl's thinking")
        return owl.answer_for(prompt)

    def _parrot_complete(self, prompt: str, timeout: float) -> str:
        self.clock.sleep(PARROT_SECONDS)
        return "Squawk! " + owl.answer_for(prompt).split("\n", 1)[0]

    def ask(self, question: str, outcome: AskOutcome) -> None:
        loaded = False

        def load() -> dict[str, str]:
            nonlocal loaded
            loaded = True
            provider, answer = self._call_providers(question, outcome)
            outcome.cost += OWL_COST if provider == "owl" else PARROT_COST
            return {"provider": provider, "answer": answer}

        messages = [{"role": "user", "content": question.strip().lower()}]
        try:
            key = self.caching.llm_cache_key("owl-large", messages, temperature=0.0)
        except NotImplementedError:
            key = None
            add_note(outcome.notes, "no LLM cache key: every question goes to a model")

        result: dict[str, str] | None = None
        if key is not None:
            try:
                result = self.cache.get_or_load(key, load)
            except NotImplementedError:
                add_note(outcome.notes, "no cache: every question goes to a model")
        if result is None:
            result = load()

        outcome.cache_hit = not loaded
        outcome.provider = "cache" if outcome.cache_hit else result["provider"]
        outcome.answer = result["answer"]

    def _call_providers(self, question: str, outcome: AskOutcome) -> tuple[str, str]:
        try:
            return self.reliability.complete_with_fallback(
                question, self.providers, self.breakers, self.policy, timeout=3.0
            )
        except NotImplementedError:
            add_note(outcome.notes, "no retry or fallback: one long call to the Owl")
            return "owl", self._owl_complete(question, NAIVE_TIMEOUT)


class FoodBowls:
    """Feeding orders through a lossy network (level 04)."""

    def __init__(self, rng: random.Random) -> None:
        self.idem = level_module("l04_idempotency.idempotency")
        self.db = self.idem.connect()
        self.store = self.idem.IdempotencyStore(self.db)
        self.rng = rng
        self.orders = 0

    def feed(self, animal: str, outcome: FeedOutcome) -> None:
        outcome.attempts = self.rng.choice([1, 2, 2, 3, 3])
        self.orders += 1
        order_id = f"{animal}-{self.orders}"
        payload = {"animal": animal, "grams": MEAL_GRAMS, "order_id": order_id}
        before = self.idem.belly(self.db, animal)
        serve = functools.partial(self._serve, order_id, animal, outcome)

        for _ in range(outcome.attempts):
            try:
                response = self.store.execute(f"idem-{order_id}", payload, serve)
                outcome.replays += int(response.replayed)
            except NotImplementedError:
                add_note(outcome.notes, "no Idempotency-Key: every retry runs the order again")
                serve()
            except Exception as exc:  # noqa: BLE001 - a learner bug becomes a game event
                add_note(outcome.notes, f"food bowl crashed: {type(exc).__name__}: {exc}")
        outcome.delivered_grams = self.idem.belly(self.db, animal) - before

    def _serve(self, order_id: str, animal: str, outcome: FeedOutcome) -> Any:
        try:
            self.idem.record_meal(self.db, order_id, animal, MEAL_GRAMS)
        except NotImplementedError:
            add_note(outcome.notes, "no UNIQUE order guard in the database")
            self.db.execute(
                "INSERT INTO bellies (cat, grams_eaten) VALUES (?, ?) ON CONFLICT(cat) "
                "DO UPDATE SET grams_eaten = grams_eaten + excluded.grams_eaten",
                (animal, MEAL_GRAMS),
            )
        return self.idem.StoredResponse(201, {"served": MEAL_GRAMS})


class GameBackend:
    """Every live call runs on one dedicated thread: the learner's SQLite connections are
    created with the default check_same_thread=True, and the game state needs no locks."""

    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="zoo-backend")
        self._rng = random.Random()
        self._kiosk: Kiosk | None = None
        self._bowls: FoodBowls | None = None

    async def run(self, function: Callable[..., T], *args: Any) -> T:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, functools.partial(function, *args))

    def reset(self) -> None:
        self._kiosk = None
        self._bowls = None

    def ask(self, question: str, storm: bool) -> AskOutcome:
        outcome = AskOutcome()
        try:
            kiosk = self._kiosk = self._kiosk or Kiosk(self._rng)
        except Exception as exc:  # noqa: BLE001 - a file that does not import
            return self._crashed(outcome, "the kiosk code does not load", exc)
        kiosk.storm = storm
        started = kiosk.clock()
        try:
            kiosk.ask(question, outcome)
        except kiosk.reliability.AllProvidersFailed:
            outcome.failed = True
            add_note(outcome.notes, "every model failed")
        except kiosk.reliability.TransientError as exc:
            outcome.failed = True
            add_note(outcome.notes, f"the Owl never answered: {exc}")
        except Exception as exc:  # noqa: BLE001 - a learner bug becomes a game event
            self._crashed(outcome, "the kiosk crashed", exc)
        outcome.sim_seconds = kiosk.clock() - started
        return outcome

    def feed(self, animal: str) -> FeedOutcome:
        outcome = FeedOutcome()
        try:
            bowls = self._bowls = self._bowls or FoodBowls(self._rng)
            bowls.feed(animal, outcome)
        except Exception as exc:  # noqa: BLE001 - a file that does not import
            add_note(outcome.notes, f"the food bowl code does not load: {exc}")
        return outcome

    @staticmethod
    def _crashed(outcome: AskOutcome, what: str, exc: Exception) -> AskOutcome:
        outcome.failed = True
        add_note(outcome.notes, f"{what}: {type(exc).__name__}: {exc}")
        return outcome
