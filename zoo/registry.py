"""Single source of truth for the ten levels: metadata, file locations and scene loading."""

from __future__ import annotations

import importlib
import re
from dataclasses import dataclass
from pathlib import Path

from zoo.kit import Event, SceneResult, run_scene

ROOT = Path(__file__).resolve().parent.parent
LEVELS_DIR = ROOT / "levels"
_TODO_PATTERN = re.compile(r'raise NotImplementedError\("([^"]+)"\)')


@dataclass(frozen=True)
class Level:
    number: int
    slug: str
    pattern: str
    station: str
    keeper: str
    animal: str
    pitch: str
    todo_file: str
    todos: tuple[str, ...]
    victory: str

    @property
    def id(self) -> str:
        return f"{self.number:02d}"

    @property
    def folder(self) -> Path:
        return LEVELS_DIR / self.slug

    @property
    def todo_path(self) -> Path:
        return self.folder / self.todo_file

    def todos_left(self) -> list[str]:
        """Names still raising NotImplementedError in the learner file."""
        try:
            source = self.todo_path.read_text(encoding="utf-8")
        except OSError:
            return list(self.todos)
        return _TODO_PATTERN.findall(source)

    def to_public_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "number": self.number,
            "slug": self.slug,
            "pattern": self.pattern,
            "station": self.station,
            "keeper": self.keeper,
            "animal": self.animal,
            "pitch": self.pitch,
            "file": f"levels/{self.slug}/{self.todo_file}",
            "todos": list(self.todos),
            "todos_left": self.todos_left(),
        }


LEVELS: tuple[Level, ...] = (
    Level(
        1,
        "l01_cache",
        "Cache",
        "The Nut Store",
        "Hazel the squirrel",
        "squirrel",
        "Hazel keeps the Owl's answers in her nut store so visitors do not wait for the slow, "
        "expensive Owl every time.",
        "cache.py",
        ("CacheAside.get_or_load", "CacheAside.invalidate", "llm_cache_key", "embed_many"),
        "Hazel serves repeated questions from the nut store. The Owl only works on new ones.",
    ),
    Level(
        2,
        "l02_rate_limit",
        "Rate limiting + API gateway",
        "The Gate",
        "Gus the goose",
        "goose",
        "Gus guards the gate in front of the Owl. A pigeon flock spams requests and a python "
        "sends giant prompts.",
        "rate_limit.py",
        (
            "TokenBucket.refill",
            "TokenBucket.try_consume",
            "TokenBucket.retry_after",
            "RateLimiter.check",
        ),
        "Gus lets the hedgehog through and throttles the pigeons. The Owl stays calm.",
    ),
    Level(
        3,
        "l03_reliability",
        "Reliability of external calls",
        "The Bridge",
        "Rusty the fox",
        "fox",
        "Rusty carries questions across the bridge to the Owl. A storm hits: the Owl stops "
        "answering and the Parrot is the backup model.",
        "reliability.py",
        (
            "backoff_delay",
            "retry",
            "CircuitBreaker.allow_request",
            "CircuitBreaker.record_success",
            "CircuitBreaker.record_failure",
            "complete_with_fallback",
        ),
        "Rusty retries with jitter, stops hammering the dead Owl and falls back to the Parrot.",
    ),
    Level(
        4,
        "l04_idempotency",
        "Idempotency",
        "The Food Bowl",
        "Miso the cat",
        "cat",
        "Miso orders meals through a flaky network. Every lost response triggers a retry. "
        "Without idempotency, Miso eats everything twice.",
        "idempotency.py",
        ("fingerprint", "IdempotencyStore.execute", "record_meal"),
        "Every meal is served exactly once, no matter how often the client retries.",
    ),
    Level(
        5,
        "l05_observability",
        "Observability",
        "The Lookout",
        "Mika the meerkat",
        "meerkat",
        "Mika watches the zoo from the lookout: JSON logs, request ids, p95 latency and SLO "
        "alerts when the sloth exhibit gets slow.",
        "observability.py",
        ("request_context", "JsonFormatter.format", "percentile", "burn_rate", "should_page"),
        "Mika traces every request, spots the slow sloth path and pages only on real incidents.",
    ),
    Level(
        6,
        "l06_db_performance",
        "Database performance",
        "The Burrows",
        "Digby the mole",
        "mole",
        "Digby digs through the animal registry. Every useless query is one more tunnel.",
        "db_performance.py",
        ("index_statements", "catalog_page", "animals_with_enclosure", "ConnectionPool.connection"),
        "Digby reads the catalog with one index, one query per page and a shared pool.",
    ),
    Level(
        7,
        "l07_data_integrity",
        "Data integrity",
        "The Dam",
        "Bea the beaver",
        "beaver",
        "Bea keeps the books straight: food moves between pantries, two families try to adopt "
        "the same kitten, and a column migrates while the zoo stays open.",
        "integrity.py",
        ("transfer_food", "adopt", "backfill_in_batches"),
        "No food is created or lost, each kitten has one family, the migration never blocks.",
    ),
    Level(
        8,
        "l08_async",
        "Async processing",
        "The Anthill",
        "The ant colony",
        "ant",
        "Ants carry background jobs. Rotten leaves (poison jobs) must go to the lost and "
        "found instead of blocking the colony. The Owl streams its answers word by word.",
        "async_jobs.py",
        ("Worker.run_once", "sse_event"),
        "The colony delivers every job, quarantines poison ones and streams the Owl live.",
    ),
    Level(
        9,
        "l09_auth",
        "Auth + security",
        "The Kennel",
        "Rex the guard dog",
        "dog",
        "Rex checks every badge. A raccoon from the Lyon shelter tries to read the Paris "
        "shelter's animals with forged and expired tokens.",
        "auth.py",
        ("verify_token", "ApiKeyStore.authenticate", "authorize"),
        "Rex lets keepers in and keeps the raccoon out of every other tenant.",
    ),
    Level(
        10,
        "l10_deploy",
        "Deployment + scaling",
        "The Nest",
        "Pip the canary",
        "canary",
        "Pip tests every new release first. A bad song version must roll back, a good one "
        "must ship, and shutting down must never drop a request.",
        "deploy.py",
        (
            "in_canary",
            "judge_canary",
            "Lifecycle.ready",
            "Lifecycle.track_request",
            "Lifecycle.begin_shutdown",
            "Lifecycle.wait_until_drained",
        ),
        "Pip rolls back the broken release, promotes the good one and drains cleanly.",
    ),
)


def find_level(key: str | int) -> Level:
    """Accept 3, "3", "03" or "l03_reliability"."""
    text = str(key).strip().lower()
    for level in LEVELS:
        if text in {level.id, str(level.number), level.slug}:
            return level
    raise KeyError(f"unknown level {key!r}, expected 1 to {len(LEVELS)}")


def play_level(level: Level) -> SceneResult:
    try:
        module = importlib.import_module(f"levels.{level.slug}.scene")
    except Exception as exc:  # noqa: BLE001 - a typo in a level must not take the game down
        headline = f"{level.todo_file} does not load: {type(exc).__name__}: {exc}"
        return SceneResult(level.id, "broken", headline, [Event("bad", headline)], {})
    return run_scene(level.id, module.play, level.victory)
