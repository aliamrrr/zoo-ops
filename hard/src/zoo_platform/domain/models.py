"""Domain objects. Plain data, no I/O."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    tenant: str
    scopes: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class Answer:
    text: str
    model: str


@dataclass(frozen=True, slots=True)
class Animal:
    id: int
    tenant: str
    name: str
    species: str
    enclosure_id: int
    arrived_at: int


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    id: int
    name: str
    species: str
    enclosure: str
    arrived_at: int


@dataclass(frozen=True, slots=True)
class CatalogPage:
    items: list[CatalogEntry]
    next_offset: int | None


@dataclass(frozen=True, slots=True)
class MealOrder:
    order_id: str
    animal_id: int
    grams: int


@dataclass(frozen=True, slots=True)
class SupplierDelivery:
    reference: str
    animal_id: int
    grams: int


@dataclass(frozen=True, slots=True)
class Kitten:
    id: str
    tenant: str
    name: str
    adopted_by: str | None


@dataclass(frozen=True, slots=True)
class Pantry:
    id: str
    tenant: str
    food_kg: int


@dataclass(frozen=True, slots=True)
class Pen:
    id: str
    tenant: str
    dirty: bool


@dataclass(slots=True)
class Job:
    id: str
    kind: str
    payload: dict[str, Any] = field(default_factory=dict)
    attempts: int = 0
    last_error: str | None = None
