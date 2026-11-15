"""The night watch: one scheduler instance must run the nightly feeding, never two."""

from __future__ import annotations

from dataclasses import dataclass

from zoo_planet.sim import Clock

LEASE_NAME = "nightly-feeding"
LEASE_TTL_S = 10.0


class LeaseStore:
    """A coordination service (think etcd or ZooKeeper)."""

    def __init__(self, clock: Clock) -> None:
        self._clock = clock

    def acquire(self, name: str, owner: str, ttl_s: float) -> int | None:
        """Try to hold lease `name` for `ttl_s` seconds. Returns a token when granted."""
        return 1


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    writer: str
    token: int | None
    portion: str


class FeedingLedger:
    """The food dispensers. Every entry releases real food."""

    def __init__(self) -> None:
        self.entries: list[LedgerEntry] = []

    def write(self, writer: str, portion: str, token: int | None = None) -> None:
        self.entries.append(LedgerEntry(writer, token, portion))


class NightlyScheduler:
    def __init__(self, name: str, leases: LeaseStore, ledger: FeedingLedger) -> None:
        self.name = name
        self._leases = leases
        self._ledger = ledger

    def tick(self) -> bool:
        """Called every second on every instance. True when this instance fed the animals."""
        token = self._leases.acquire(LEASE_NAME, self.name, LEASE_TTL_S)
        if token is None:
            return False
        self._ledger.write(self.name, "one scoop", token)
        return True
