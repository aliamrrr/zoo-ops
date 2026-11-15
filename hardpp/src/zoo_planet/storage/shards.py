"""The animal registry, split across database shards."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AnimalRecord:
    id: str
    species: str
    arrived_at: int


class Shard:
    """One database server. Counts how many rows it had to read."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.rows: dict[str, AnimalRecord] = {}
        self.rows_read = 0

    def put(self, record: AnimalRecord) -> None:
        self.rows[record.id] = record

    def get(self, animal_id: str) -> AnimalRecord | None:
        self.rows_read += 1
        return self.rows.get(animal_id)

    def delete(self, animal_id: str) -> None:
        self.rows.pop(animal_id, None)

    def newest(
        self, species: str, limit: int, before: tuple[int, str] | None = None
    ) -> list[AnimalRecord]:
        """Newest arrivals first (arrived_at desc, then id desc), strictly before `before`.

        Served by an index."""
        matches = sorted(
            (r for r in self.rows.values() if r.species == species),
            key=lambda r: (r.arrived_at, r.id),
            reverse=True,
        )
        if before is not None:
            matches = [r for r in matches if (r.arrived_at, r.id) < before]
        page = matches[:limit]
        self.rows_read += len(page)
        return page


def stable_hash(key: str) -> int:
    return int.from_bytes(hashlib.md5(key.encode()).digest()[:8], "big")


class ShardRouter:
    def __init__(self, shards: list[Shard]) -> None:
        self.shards = list(shards)

    def shard_for(self, key: str) -> Shard:
        return self.shards[stable_hash(key) % len(self.shards)]

    def add(self, shard: Shard) -> None:
        self.shards.append(shard)


class AnimalRegistry:
    def __init__(self, router: ShardRouter) -> None:
        self.router = router

    def put(self, record: AnimalRecord) -> None:
        self.router.shard_for(record.id).put(record)

    def get(self, animal_id: str) -> AnimalRecord | None:
        return self.router.shard_for(animal_id).get(animal_id)

    def add_shard(self, shard: Shard) -> None:
        self.router.add(shard)

    def rebalance(self, batch: int = 100) -> int:
        """Move up to `batch` misplaced records to their owner. Returns how many moved."""
        return 0

    def newest(
        self, species: str, limit: int, cursor: str | None = None
    ) -> tuple[list[AnimalRecord], str | None]:
        everything: list[AnimalRecord] = []
        for shard in self.router.shards:
            everything.extend(shard.newest(species, 1_000_000))
        everything.sort(key=lambda r: (r.arrived_at, r.id), reverse=True)
        offset = int(cursor or 0)
        page = everything[offset : offset + limit]
        more = offset + limit < len(everything)
        return page, str(offset + limit) if more else None
