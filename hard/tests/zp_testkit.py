"""Test doubles and helpers for the Zoo Platform test suite."""

from __future__ import annotations

import io
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import fakeredis
import jwt
from fastapi.testclient import TestClient

from zoo_platform.api.app import create_app
from zoo_platform.container import Adapters, Container, build_container
from zoo_platform.domain.errors import CrewBusy, ProviderRejected, ProviderUnavailable
from zoo_platform.infrastructure.database import sqlite_factory
from zoo_platform.ports import CompletionRequest, CompletionResult
from zoo_platform.settings import Settings

SECRET = "test-signing-secret-with-enough-entropy-0123456789"
ALL_SCOPES = ("kitchen:write", "staff")
SPECIES = ("cat", "fox", "otter", "lion", "penguin")


class FakeClock:
    def __init__(self, start: float = 1_000_000.0) -> None:
        self.now = start
        self.sleeps: list[float] = []
        self._lock = threading.Lock()

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        with self._lock:
            self.now += seconds

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.advance(seconds)


class ModelStub:
    """A scripted language model. Records every request it receives."""

    def __init__(self, name: str, clock: FakeClock) -> None:
        self.name = name
        self.clock = clock
        self.requests: list[CompletionRequest] = []
        self.outage = False
        self.reject = False
        self.failures_left = 0
        self.fail_models: set[str] = set()
        self.latency_s = 0.0
        self.suffix = ""
        self.gate: threading.Event | None = None
        self._lock = threading.Lock()

    def complete(self, request: CompletionRequest) -> CompletionResult:
        with self._lock:
            self.requests.append(request)
            failing = self.failures_left > 0
            if failing:
                self.failures_left -= 1
        if self.gate is not None:
            self.gate.wait(10)
        if self.latency_s:
            self.clock.advance(self.latency_s)
        if self.reject:
            raise ProviderRejected(f"{self.name} refused the prompt")
        if self.outage or failing or request.model in self.fail_models:
            raise ProviderUnavailable(f"{self.name} is unavailable")
        fact = (
            request.prompt.split("Fact: ", 1)[1].split("\n", 1)[0]
            if "Fact: " in request.prompt
            else "?"
        )
        return CompletionResult(text=f"{self.name} says: {fact}{self.suffix}", model=request.model)


class CrewStub:
    def __init__(self) -> None:
        self.dispatched: list[str] = []
        self.busy: dict[str, int] = {}

    def dispatch(self, pen_id: str) -> None:
        self.dispatched.append(pen_id)
        remaining = self.busy.get(pen_id, 0)
        if remaining:
            if remaining > 0:
                self.busy[pen_id] = remaining - 1
            raise CrewBusy(f"no robot available for {pen_id}")


@dataclass
class World:
    """One isolated zoo: its database, its Redis, its models, and the clients talking to it."""

    root: Path
    overrides: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.clock = FakeClock()
        self.redis = fakeredis.FakeRedis()
        self.owl = ModelStub("owl", self.clock)
        self.parrot = ModelStub("parrot", self.clock)
        self.crew = CrewStub()
        self.db_path = str(self.root / "zoo.db")
        self.logs = io.StringIO()
        self.connections_opened = 0
        self.statements: list[str] = []
        self.containers: list[Container] = []
        self._client: TestClient | None = None
        self._seeded = False
        self._seed_lock = threading.Lock()

    @property
    def settings(self) -> Settings:
        return Settings(jwt_secret=SECRET, database_path=self.db_path, **self.overrides)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite_factory(self.db_path)()
        self.connections_opened += 1
        conn.set_trace_callback(self.statements.append)
        return conn

    def adapters(self) -> Adapters:
        return Adapters(
            clock=self.clock,
            sleep=self.clock.sleep,
            redis=self.redis,
            owl=self.owl,
            parrot=self.parrot,
            crew=self.crew,
            connect=self.connect,
            log_stream=self.logs,
        )

    def replica(self) -> TestClient:
        """A new instance of the service sharing this world's database, Redis and models."""
        container = build_container(self.settings, self.adapters())
        self.containers.append(container)
        with self._seed_lock:
            if not self._seeded:
                seed(self.db_path)
                self._seeded = True
        return TestClient(create_app(container))

    @property
    def client(self) -> TestClient:
        if self._client is None:
            self._client = self.replica()
        return self._client

    def sql(self, query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        self.client  # noqa: B018 - the schema exists once the service has started
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(query, params).fetchall()
            conn.commit()
            return rows
        finally:
            conn.close()


def seed(db_path: str) -> None:
    conn = sqlite3.connect(db_path, timeout=10)
    try:
        conn.executemany(
            "INSERT INTO enclosures (id, name) VALUES (?, ?)",
            [(i, f"Enclosure {i}") for i in range(1, 7)],
        )
        conn.executemany(
            "INSERT INTO animals (tenant, name, species, enclosure_id, arrived_at) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                (
                    "paris",
                    f"{SPECIES[i % 5]}-{i}",
                    SPECIES[i % 5],
                    1 + i % 6,
                    1_000 + (i * 7_919) % 5_000,
                )
                for i in range(400)
            ]
            + [("lyon", f"lyon-cat-{i}", "cat", 1, 2_000 + i) for i in range(30)],
        )
        conn.executemany(
            "INSERT INTO facts (topic, text, updated_at) VALUES (?, ?, 0)",
            [
                ("otter", "Sea otters hold hands while they sleep."),
                ("lion", "Lions sleep up to 20 hours a day."),
                ("penguin", "Penguins propose with a pebble."),
                ("fox", "A fox can hear a watch ticking 40 meters away."),
            ],
        )
        conn.executemany(
            "INSERT INTO kittens (id, tenant, name) VALUES (?, ?, ?)",
            [("pixel", "paris", "Pixel"), ("mochi", "paris", "Mochi"), ("luna", "lyon", "Luna")],
        )
        conn.executemany(
            "INSERT INTO pantries (id, tenant, food_kg) VALUES (?, ?, ?)",
            [
                ("north", "paris", 100),
                ("south", "paris", 100),
                ("east", "paris", 0),
                ("rhone", "lyon", 50),
            ],
        )
        conn.executemany(
            "INSERT INTO pens (id, tenant) VALUES (?, ?)",
            [
                ("pen-lion", "paris"),
                ("pen-otter", "paris"),
                ("pen-penguin", "paris"),
                ("pen-rhone", "lyon"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def token(
    subject: str = "visitor-1",
    tenant: str = "paris",
    scopes: tuple[str, ...] = ALL_SCOPES,
    ttl_s: int = 3_600,
    secret: str = SECRET,
    **claims: Any,
) -> str:
    now = int(time.time())
    payload = {
        "sub": subject,
        "tenant": tenant,
        "scopes": list(scopes),
        "iat": now,
        "exp": now + ttl_s,
    }
    payload.update(claims)
    return jwt.encode(payload, secret, algorithm="HS256")


def auth(subject: str = "visitor-1", tenant: str = "paris", **kwargs: Any) -> dict[str, str]:
    return {"Authorization": f"Bearer {token(subject, tenant, **kwargs)}"}


def ask(
    client: TestClient,
    question: str,
    user: str = "visitor-1",
    temperature: float = 0.0,
    headers: dict[str, str] | None = None,
):  # type: ignore[no-untyped-def]
    return client.post(
        "/v1/owl/answers",
        json={"question": question, "temperature": temperature},
        headers={**auth(user), **(headers or {})},
    )


def parse_sse(body: str) -> list[dict[str, str]]:
    events = []
    for block in body.replace("\r\n", "\n").split("\n\n"):
        if not block.strip():
            continue
        event = {"event": "message"}
        data: list[str] = []
        for line in block.split("\n"):
            name, _, value = line.partition(":")
            value = value[1:] if value.startswith(" ") else value
            if name == "data":
                data.append(value)
            elif name in {"event", "id"}:
                event[name] = value
        event["data"] = "\n".join(data)
        events.append(event)
    return events
