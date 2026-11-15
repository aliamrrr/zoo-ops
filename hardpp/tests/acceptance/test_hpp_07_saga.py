"""Ticket 07: the half-finished adoption."""

import pytest

from zoo_planet.adoption.services import Payments, Shelter, Transport
from zoo_planet.adoption.workflow import Adoption, AdoptionWorkflow, SagaStore
from zoo_planet.sim import Crash, CrashPlan

PIXEL = Adoption("adopt-1", kitten="pixel", family="martins", fee=120)


class Office:
    def __init__(self) -> None:
        self.shelter, self.payments, self.transport = Shelter(), Payments(), Transport()
        self.store, self.crash = SagaStore(), CrashPlan()

    def workflow(self) -> AdoptionWorkflow:
        """A fresh process: same services and durable store, nothing in memory."""
        return AdoptionWorkflow(self.shelter, self.payments, self.transport, self.store, self.crash)

    def calls(self, operation: str) -> int:
        every = self.shelter.calls + self.payments.calls + self.transport.calls
        return sum(1 for name, _ in every if name == operation)


def test_a_happy_adoption_completes() -> None:
    office = Office()
    assert office.workflow().run(PIXEL) == "completed"
    assert office.shelter.reserved == {"pixel": "adopt-1"}
    assert office.payments.charged == {"adopt-1": 120}
    assert office.transport.booked == {"adopt-1": "pixel"}


def test_a_refused_step_undoes_the_previous_ones() -> None:
    office = Office()
    office.transport.fail("book", permanent=True)
    assert office.workflow().run(PIXEL) == "compensated"
    assert office.shelter.reserved == {}
    assert office.payments.charged == {}
    assert office.payments.balance["martins"] == 0
    assert office.calls("refund") == 1
    assert office.calls("release") == 1


def test_transient_failures_are_retried_before_giving_up() -> None:
    office = Office()
    office.payments.fail("charge", transient=2)
    assert office.workflow().run(PIXEL) == "completed"
    assert office.payments.charged == {"adopt-1": 120}


def test_a_crash_after_charging_resumes_and_finishes() -> None:
    office = Office()
    office.crash.arm("saga.after_charge")
    with pytest.raises(Crash):
        office.workflow().run(PIXEL)
    assert office.workflow().resume() == {"adopt-1": "completed"}
    assert office.transport.booked == {"adopt-1": "pixel"}
    assert office.calls("charge") == 1, "a completed step is never repeated"
    assert office.calls("reserve") == 1


def test_a_crash_while_compensating_resumes_the_compensation() -> None:
    office = Office()
    office.transport.fail("book", permanent=True)
    office.payments.fail("refund", transient=1)
    office.crash.arm("saga.compensating")
    with pytest.raises(Crash):
        office.workflow().run(PIXEL)
    assert office.workflow().resume() == {"adopt-1": "compensated"}
    assert office.payments.charged == {}
    assert office.shelter.reserved == {}


def test_status_is_queryable_from_any_process() -> None:
    office = Office()
    office.workflow().run(PIXEL)
    assert office.workflow().status("adopt-1") == "completed"
