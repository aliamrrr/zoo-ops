"""International adoptions: reserve the kitten, charge the family, book the van."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from zoo_planet.adoption.services import Payments, Shelter, Transport
from zoo_planet.sim import CrashPlan


@dataclass(frozen=True, slots=True)
class Adoption:
    id: str
    kitten: str
    family: str
    fee: int


class SagaStore:
    """Durable storage for workflow state. It survives the crashes of the simulation."""

    def __init__(self) -> None:
        self.records: dict[str, dict[str, Any]] = {}


class AdoptionWorkflow:
    def __init__(
        self,
        shelter: Shelter,
        payments: Payments,
        transport: Transport,
        store: SagaStore,
        crash: CrashPlan,
    ) -> None:
        self._shelter = shelter
        self._payments = payments
        self._transport = transport
        self._store = store
        self._crash = crash

    def run(self, adoption: Adoption) -> str:
        self._shelter.reserve(adoption.id, adoption.kitten)
        self._crash.point("saga.after_reserve")
        self._payments.charge(adoption.id, adoption.family, adoption.fee)
        self._crash.point("saga.after_charge")
        self._transport.book(adoption.id, adoption.kitten)
        return "completed"

    def resume(self) -> dict[str, str]:
        """Called when the process restarts. Returns the final status of each adoption."""
        return {}

    def status(self, adoption_id: str) -> str | None:
        record = self._store.records.get(adoption_id)
        return None if record is None else str(record.get("status"))
