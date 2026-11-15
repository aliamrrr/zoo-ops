"""Ticket 08: events out of order."""

import pytest

from zoo_planet.stream.log import ConsumerGroup, PartitionedLog


def produce(log: PartitionedLog, animals: int = 12, events: int = 10) -> None:
    for step in range(events):
        for a in range(animals):
            log.append(f"animal-{a}", {"animal": f"animal-{a}", "step": step})


def consume(
    group: ConsumerGroup, member: str, seen: dict[str, list[int]], crash_after: int | None = None
) -> int:
    records = group.poll(member, max_records=5)
    progress: dict[int, int] = {}
    for handled, record in enumerate(records):
        if crash_after is not None and handled == crash_after:
            break
        seen.setdefault(record.key, []).append(record.value["step"])
        progress[record.partition] = record.offset + 1
    if crash_after is None:
        for partition, offset in progress.items():
            group.commit(member, partition, offset)
    return len(records)


def test_events_of_one_animal_keep_their_order() -> None:
    log = PartitionedLog(partitions=5)
    produce(log)
    group = ConsumerGroup(log, "keepers")
    for member in ("a", "b", "c"):
        group.join(member)
    seen: dict[str, list[int]] = {}
    for _ in range(100):
        if not any(consume(group, m, seen) for m in ("a", "b", "c")):
            break
    assert all(steps == list(range(10)) for steps in seen.values()), seen
    assert len(seen) == 12


def test_every_partition_has_exactly_one_owner_after_a_rebalance() -> None:
    log = PartitionedLog(partitions=7)
    group = ConsumerGroup(log, "keepers")
    for member in ("a", "b", "c"):
        group.join(member)
    group.leave("b")
    group.join("d")
    owned = [p for member in group.members for p in group.assignment[member]]
    assert sorted(owned) == list(range(7))
    sizes = [len(group.assignment[member]) for member in group.members]
    assert max(sizes) - min(sizes) <= 1


def test_a_consumer_crash_loses_nothing() -> None:
    log = PartitionedLog(partitions=2)
    produce(log, animals=4, events=6)
    group = ConsumerGroup(log, "keepers")
    group.join("a")
    group.join("b")
    seen: dict[str, list[int]] = {}
    consume(group, "a", seen, crash_after=2)
    group.leave("a")
    for _ in range(50):
        if not consume(group, "b", seen):
            break
    assert all(sorted(set(steps)) == list(range(6)) for steps in seen.values())
    assert all(steps == sorted(steps) for steps in seen.values()), "redelivery keeps the order"


def test_a_zombie_cannot_commit_after_losing_its_partition() -> None:
    log = PartitionedLog(partitions=2)
    produce(log, animals=4, events=2)
    group = ConsumerGroup(log, "keepers")
    group.join("a")
    records = group.poll("a", max_records=3)
    group.join("b")
    lost = [r for r in records if r.partition not in group.assignment["a"]]
    assert lost, "the rebalance moved one of a's partitions to b"
    with pytest.raises(Exception, match="(?i)owner"):
        group.commit("a", lost[0].partition, lost[0].offset + 1)
