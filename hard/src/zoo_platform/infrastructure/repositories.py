"""Repositories: the only place that knows SQL."""

from __future__ import annotations

import sqlite3

from zoo_platform.domain.errors import NotFound
from zoo_platform.domain.models import Animal, Kitten, Pantry, Pen
from zoo_platform.infrastructure.database import Database


def _animal(row: sqlite3.Row) -> Animal:
    return Animal(
        row["id"],
        row["tenant"],
        row["name"],
        row["species"],
        row["enclosure_id"],
        row["arrived_at"],
    )


class AnimalRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def add(self, tenant: str, name: str, species: str, enclosure_id: int, arrived_at: int) -> int:
        with self._db.session() as conn:
            cursor = conn.execute(
                "INSERT INTO animals (tenant, name, species, enclosure_id, arrived_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (tenant, name, species, enclosure_id, arrived_at),
            )
            return int(cursor.lastrowid or 0)

    def get(self, animal_id: int) -> Animal:
        with self._db.session() as conn:
            row = conn.execute("SELECT * FROM animals WHERE id = ?", (animal_id,)).fetchone()
        if row is None:
            raise NotFound(f"animal {animal_id}")
        return _animal(row)

    def list_by_species(self, species: str, offset: int, limit: int) -> list[Animal]:
        with self._db.session() as conn:
            rows = conn.execute(
                "SELECT * FROM animals WHERE species = ? "
                "ORDER BY arrived_at DESC, id DESC LIMIT ? OFFSET ?",
                (species, limit, offset),
            ).fetchall()
        return [_animal(row) for row in rows]

    def enclosure_name(self, enclosure_id: int) -> str:
        with self._db.session() as conn:
            row = conn.execute(
                "SELECT name FROM enclosures WHERE id = ?", (enclosure_id,)
            ).fetchone()
        if row is None:
            raise NotFound(f"enclosure {enclosure_id}")
        return str(row["name"])


class FactRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def get(self, topic: str) -> str | None:
        with self._db.session() as conn:
            row = conn.execute("SELECT text FROM facts WHERE topic = ?", (topic,)).fetchone()
        return None if row is None else str(row["text"])

    def upsert(self, topic: str, text: str, now: int) -> None:
        with self._db.session() as conn:
            conn.execute(
                "INSERT INTO facts (topic, text, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT (topic) DO UPDATE SET text = excluded.text, "
                "updated_at = excluded.updated_at",
                (topic, text, now),
            )


class KitchenRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def record_meal(
        self, animal_id: int, grams: int, now: int, supplier_ref: str | None = None
    ) -> int:
        with self._db.session() as conn:
            cursor = conn.execute(
                "INSERT INTO meals (animal_id, grams, supplier_ref, created_at) "
                "VALUES (?, ?, ?, ?)",
                (animal_id, grams, supplier_ref, now),
            )
            conn.execute(
                "INSERT INTO bellies (animal_id, grams) VALUES (?, ?) "
                "ON CONFLICT (animal_id) DO UPDATE SET grams = grams + excluded.grams",
                (animal_id, grams),
            )
            return int(cursor.lastrowid or 0)

    def belly(self, animal_id: int) -> int:
        with self._db.session() as conn:
            row = conn.execute(
                "SELECT grams FROM bellies WHERE animal_id = ?", (animal_id,)
            ).fetchone()
        return 0 if row is None else int(row["grams"])


class KittenRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def add(self, tenant: str, kitten_id: str, name: str) -> None:
        with self._db.session() as conn:
            conn.execute(
                "INSERT INTO kittens (id, tenant, name) VALUES (?, ?, ?)", (kitten_id, tenant, name)
            )

    def get(self, kitten_id: str) -> Kitten:
        with self._db.session() as conn:
            row = conn.execute("SELECT * FROM kittens WHERE id = ?", (kitten_id,)).fetchone()
        if row is None:
            raise NotFound(f"kitten {kitten_id}")
        return Kitten(row["id"], row["tenant"], row["name"], row["adopted_by"])

    def set_adopter(self, kitten_id: str, family: str) -> None:
        with self._db.session() as conn:
            conn.execute("UPDATE kittens SET adopted_by = ? WHERE id = ?", (family, kitten_id))


class PantryRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def get(self, pantry_id: str) -> Pantry:
        with self._db.session() as conn:
            row = conn.execute("SELECT * FROM pantries WHERE id = ?", (pantry_id,)).fetchone()
        if row is None:
            raise NotFound(f"pantry {pantry_id}")
        return Pantry(row["id"], row["tenant"], row["food_kg"])

    def set_food(self, pantry_id: str, food_kg: int) -> None:
        with self._db.session() as conn:
            conn.execute("UPDATE pantries SET food_kg = ? WHERE id = ?", (food_kg, pantry_id))


class PenRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def get(self, pen_id: str) -> Pen:
        with self._db.session() as conn:
            row = conn.execute("SELECT * FROM pens WHERE id = ?", (pen_id,)).fetchone()
        if row is None:
            raise NotFound(f"pen {pen_id}")
        return Pen(row["id"], row["tenant"], bool(row["dirty"]))

    def set_dirty(self, pen_id: str, dirty: bool) -> None:
        with self._db.session() as conn:
            conn.execute("UPDATE pens SET dirty = ? WHERE id = ?", (int(dirty), pen_id))
