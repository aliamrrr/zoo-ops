"""Ticket 10: two night watchmen."""

import pytest

from zoo_planet.coordination.leases import LEASE_NAME, FeedingLedger, LeaseStore, NightlyScheduler
from zoo_planet.sim import SimClock


def night(
    clock: SimClock,
    schedulers: list[NightlyScheduler],
    seconds: int,
    paused: frozenset[str] = frozenset(),
) -> None:
    for _ in range(seconds):
        for scheduler in schedulers:
            if scheduler.name not in paused:
                scheduler.tick()
        clock.advance(1)


def crew(clock: SimClock) -> tuple[LeaseStore, FeedingLedger, list[NightlyScheduler]]:
    leases, ledger = LeaseStore(clock), FeedingLedger()
    return (
        leases,
        ledger,
        [NightlyScheduler(name, leases, ledger) for name in ("north", "south", "east")],
    )


def test_only_one_instance_feeds() -> None:
    clock = SimClock()
    _, ledger, schedulers = crew(clock)
    night(clock, schedulers, 30)
    assert len({entry.writer for entry in ledger.entries}) == 1
    assert len(ledger.entries) == 30


def test_a_lease_is_exclusive_until_it_expires() -> None:
    clock = SimClock()
    leases = LeaseStore(clock)
    first = leases.acquire(LEASE_NAME, "north", 10)
    assert first is not None
    assert leases.acquire(LEASE_NAME, "south", 10) is None
    assert leases.acquire(LEASE_NAME, "north", 10) is not None, "the holder can renew"
    clock.advance(10.5)
    second = leases.acquire(LEASE_NAME, "south", 10)
    assert second is not None and second > first, "a new holder gets a bigger fencing token"


def test_a_paused_leader_is_replaced() -> None:
    clock = SimClock()
    _, ledger, schedulers = crew(clock)
    night(clock, schedulers, 5)
    leader = ledger.entries[-1].writer
    night(clock, schedulers, 30, paused=frozenset({leader}))
    writers = [entry.writer for entry in ledger.entries]
    assert writers[-1] != leader
    assert len(set(writers[5:])) == 1, "exactly one replacement"


def test_a_stale_leader_cannot_write() -> None:
    clock = SimClock()
    leases, ledger, _ = crew(clock)
    old_token = leases.acquire(LEASE_NAME, "north", 10)
    clock.advance(15)
    new_token = leases.acquire(LEASE_NAME, "south", 10)
    ledger.write("south", "one scoop", new_token)
    with pytest.raises(Exception, match="(?i)stale|fenc"):
        ledger.write("north", "one scoop", old_token)
    assert [entry.writer for entry in ledger.entries] == ["south"]


def test_writes_without_a_token_are_refused() -> None:
    with pytest.raises(Exception, match="(?i)stale|fenc|token"):
        FeedingLedger().write("raccoon", "everything", None)
