"""Stand-ins for the external services, used when the platform runs on a laptop."""

from __future__ import annotations

import random
import time

from zoo_platform.infrastructure.database import Database
from zoo_platform.ports import CompletionRequest, CompletionResult

FACT_MARKER = "Fact: "


def fact_in(prompt: str) -> str:
    if FACT_MARKER not in prompt:
        return "I do not know that one yet."
    return prompt.split(FACT_MARKER, 1)[1].split("\n", 1)[0]


class DemoModel:
    def __init__(self, name: str, latency_s: float) -> None:
        self._name = name
        self._latency_s = latency_s

    def complete(self, request: CompletionRequest) -> CompletionResult:
        time.sleep(self._latency_s)
        return CompletionResult(text=f"Hoot. {fact_in(request.prompt)}", model=request.model)


class DemoCrew:
    def dispatch(self, pen_id: str) -> None:
        time.sleep(0.05)


SPECIES = ("cat", "fox", "otter", "lion", "penguin")


def seed_demo(db: Database) -> None:
    """Fill an empty database with one small zoo."""
    rng = random.Random(4)
    with db.session() as conn:
        if conn.execute("SELECT COUNT(*) FROM enclosures").fetchone()[0]:
            return
        conn.executemany(
            "INSERT INTO enclosures (id, name) VALUES (?, ?)",
            [(i, f"Enclosure {i}") for i in range(1, 7)],
        )
        conn.executemany(
            "INSERT INTO animals (tenant, name, species, enclosure_id, arrived_at) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                ("paris", f"{species}-{i}", species, rng.randint(1, 6), rng.randint(1_000, 9_000))
                for i in range(200)
                for species in [SPECIES[i % len(SPECIES)]]
            ],
        )
        conn.executemany(
            "INSERT INTO facts (topic, text, updated_at) VALUES (?, ?, 0)",
            [
                ("otter", "Sea otters hold hands while they sleep."),
                ("lion", "Lions sleep up to 20 hours a day."),
                ("penguin", "Penguins propose with a pebble."),
            ],
        )
        conn.execute("INSERT INTO kittens (id, tenant, name) VALUES ('pixel', 'paris', 'Pixel')")
        conn.executemany(
            "INSERT INTO pantries (id, tenant, food_kg) VALUES (?, 'paris', ?)",
            [("north", 100), ("south", 100)],
        )
        conn.executemany(
            "INSERT INTO pens (id, tenant) VALUES (?, 'paris')", [("pen-lion",), ("pen-otter",)]
        )
