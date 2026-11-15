"""Ticket 06: the registry outgrew one shard."""

import random

from zoo_planet.storage.shards import AnimalRecord, AnimalRegistry, Shard, ShardRouter

SPECIES = ("cat", "fox", "owl", "otter")


def registry(shards: int = 4, animals: int = 4_000) -> AnimalRegistry:
    rng = random.Random(6)
    reg = AnimalRegistry(ShardRouter([Shard(f"shard-{i}") for i in range(shards)]))
    for i in range(animals):
        reg.put(AnimalRecord(f"animal-{i}", SPECIES[i % 4], rng.randint(1_000, 50_000)))
    return reg


def owners(reg: AnimalRegistry, keys: list[str]) -> dict[str, str]:
    return {key: reg.router.shard_for(key).name for key in keys}


def test_adding_a_shard_moves_few_keys_and_only_to_it() -> None:
    reg = registry()
    keys = [f"animal-{i}" for i in range(4_000)]
    before = owners(reg, keys)
    reg.add_shard(Shard("shard-4"))
    after = owners(reg, keys)
    moved = [key for key in keys if before[key] != after[key]]
    assert len(moved) / len(keys) <= 0.3
    assert all(after[key] == "shard-4" for key in moved)


def test_the_ring_is_balanced() -> None:
    reg = registry(shards=5, animals=0)
    counts: dict[str, int] = {}
    for i in range(10_000):
        name = reg.router.shard_for(f"animal-{i}").name
        counts[name] = counts.get(name, 0) + 1
    assert all(1_200 <= count <= 2_800 for count in counts.values()), counts


def test_reads_stay_correct_during_an_online_reshard() -> None:
    reg = registry()
    reg.add_shard(Shard("shard-4"))
    for step in range(100):
        for i in range(0, 4_000, 37):
            assert reg.get(f"animal-{i}") is not None, f"animal-{i} vanished at step {step}"
        if reg.rebalance(batch=50) == 0:
            break
    else:
        raise AssertionError("rebalance never finished")
    shard_four = next(s for s in reg.router.shards if s.name == "shard-4")
    assert shard_four.rows, "the new shard received data"
    for shard in reg.router.shards:
        assert all(
            reg.router.shard_for(key) is shard for key in shard.rows
        ), "a key lives only on its owner"
    assert sum(len(s.rows) for s in reg.router.shards) == 4_000


def test_writes_during_a_reshard_are_not_lost() -> None:
    reg = registry()
    reg.add_shard(Shard("shard-4"))
    reg.rebalance(batch=200)
    reg.put(AnimalRecord("animal-7", "cat", 99_999))
    while reg.rebalance(batch=200):
        pass
    found = reg.get("animal-7")
    assert found is not None and found.arrived_at == 99_999


def expected_newest(reg: AnimalRegistry, species: str) -> list[str]:
    everything = [r for s in reg.router.shards for r in s.rows.values() if r.species == species]
    return [r.id for r in sorted(everything, key=lambda r: (r.arrived_at, r.id), reverse=True)]


def test_global_pages_are_merged_from_every_shard() -> None:
    reg = registry()
    seen: list[str] = []
    cursor = None
    for _ in range(200):
        page, cursor = reg.newest("fox", limit=25, cursor=cursor)
        seen.extend(r.id for r in page)
        if cursor is None:
            break
    assert seen == expected_newest(reg, "fox")


def test_a_page_reads_little_from_each_shard() -> None:
    reg = registry()
    for shard in reg.router.shards:
        shard.rows_read = 0
    page, cursor = reg.newest("cat", limit=20)
    page, _ = reg.newest("cat", limit=20, cursor=cursor)
    assert len(page) == 20
    assert sum(s.rows_read for s in reg.router.shards) <= 2 * 4 * 21
