"""Ticket 04: billed twice, or never."""

import contextlib
import importlib

import pytest

from zoo_planet.orders.broker import Broker
from zoo_planet.orders.service import (
    BILLING_SCHEMA,
    ORDERS_SCHEMA,
    BillingConsumer,
    Database,
    OrderService,
)
from zoo_planet.sim import Crash, CrashPlan


class Planet:
    def __init__(self) -> None:
        self.crash = CrashPlan()
        self.broker = Broker()
        self.orders_db = Database(ORDERS_SCHEMA)
        self.billing_db = Database(BILLING_SCHEMA)
        self.orders = OrderService(self.orders_db, self.broker, self.crash)
        self.billing = BillingConsumer(self.billing_db, self.broker, self.crash)
        relay_module = importlib.import_module("zoo_planet.orders.outbox")
        self.relay = relay_module.OutboxRelay(self.orders_db, self.broker, self.crash)

    def charged(self) -> dict[str, int]:
        rows = self.billing_db.query(
            "SELECT order_id, SUM(amount_cents) AS total FROM charges GROUP BY order_id"
        )
        return {row["order_id"]: row["total"] for row in rows}

    def settle(self) -> None:
        for _ in range(50):
            moved = self.relay.run_once()
            consumed = False
            while self.billing.poll():
                consumed = True
            if not moved and not consumed:
                return


def test_a_crash_after_commit_loses_no_event() -> None:
    planet = Planet()
    planet.crash.arm("order.after_commit")
    with pytest.raises(Crash):
        planet.orders.place("o-1", "Miso", 50, price_cents=300)
    planet.settle()
    assert planet.charged() == {"o-1": 300}


def test_an_order_that_rolls_back_publishes_nothing() -> None:
    planet = Planet()
    planet.orders.place("o-1", "Miso", 50, price_cents=300)
    with pytest.raises(Exception):  # noqa: B017 - duplicate primary key
        planet.orders.place("o-1", "Miso", 50, price_cents=300)
    planet.settle()
    assert planet.charged() == {"o-1": 300}


def test_a_relay_crash_after_publishing_does_not_double_bill() -> None:
    planet = Planet()
    planet.orders.place("o-1", "Miso", 50, price_cents=300)
    planet.crash.arm("relay.after_publish")
    with pytest.raises(Crash):
        planet.relay.run_once()
    planet.settle()
    assert len([m for m in planet.broker.published if m.body.get("order_id") == "o-1"]) == 2
    assert planet.charged() == {"o-1": 300}


def test_a_billing_crash_before_ack_does_not_double_bill() -> None:
    planet = Planet()
    planet.orders.place("o-1", "Miso", 50, price_cents=300)
    planet.relay.run_once()
    planet.crash.arm("billing.after_charge")
    with pytest.raises(Crash):
        planet.billing.poll()
    planet.broker.redeliver_unacked("orders.placed")
    planet.settle()
    assert planet.charged() == {"o-1": 300}


def test_many_orders_many_failures_exact_totals() -> None:
    planet = Planet()
    for i in range(30):
        if i % 7 == 0:
            planet.crash.arm("order.after_commit")
        with contextlib.suppress(Crash):
            planet.orders.place(f"o-{i}", "Leo", 100, price_cents=100 + i)
    planet.crash.arm("relay.after_publish", times=2)
    for _ in range(3):
        with contextlib.suppress(Crash):
            planet.relay.run_once()
    planet.crash.arm("billing.after_charge", times=3)
    for _ in range(40):
        try:
            planet.billing.poll()
        except Crash:
            planet.broker.redeliver_unacked("orders.placed")
    planet.broker.redeliver_unacked("orders.placed")
    planet.settle()
    assert planet.charged() == {f"o-{i}": 100 + i for i in range(30)}
