"""Food orders: the orders service and the billing service, each with its own database."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from zoo_planet.orders.broker import Broker, Message
from zoo_planet.sim import CrashPlan

ORDERS_TOPIC = "orders.placed"


class Database:
    """An in-memory SQLite database that survives the process 'crashes' of the simulation."""

    def __init__(self, schema: str) -> None:
        self._conn = sqlite3.connect(":memory:", check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(schema)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        self._conn.execute("BEGIN")
        try:
            yield self._conn
        except BaseException:
            self._conn.execute("ROLLBACK")
            raise
        self._conn.execute("COMMIT")

    def query(self, sql: str, params: tuple[object, ...] = ()) -> list[sqlite3.Row]:
        return self._conn.execute(sql, params).fetchall()


ORDERS_SCHEMA = """
CREATE TABLE orders (
    id TEXT PRIMARY KEY,
    animal TEXT NOT NULL,
    grams INTEGER NOT NULL,
    price_cents INTEGER NOT NULL
);
"""

BILLING_SCHEMA = """
CREATE TABLE charges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    amount_cents INTEGER NOT NULL
);
"""


class OrderService:
    def __init__(self, db: Database, broker: Broker, crash: CrashPlan) -> None:
        self._db = db
        self._broker = broker
        self._crash = crash

    def place(self, order_id: str, animal: str, grams: int, price_cents: int) -> None:
        with self._db.transaction() as conn:
            conn.execute(
                "INSERT INTO orders (id, animal, grams, price_cents) VALUES (?, ?, ?, ?)",
                (order_id, animal, grams, price_cents),
            )
        self._crash.point("order.after_commit")
        self._broker.publish(ORDERS_TOPIC, {"order_id": order_id, "price_cents": price_cents})


class BillingConsumer:
    def __init__(self, db: Database, broker: Broker, crash: CrashPlan) -> None:
        self._db = db
        self._broker = broker
        self._crash = crash

    def handle(self, message: Message) -> None:
        with self._db.transaction() as conn:
            conn.execute(
                "INSERT INTO charges (order_id, amount_cents) VALUES (?, ?)",
                (message.body["order_id"], message.body["price_cents"]),
            )
        self._crash.point("billing.after_charge")
        self._broker.ack(message)

    def poll(self) -> bool:
        message = self._broker.receive(ORDERS_TOPIC)
        if message is None:
            return False
        self.handle(message)
        return True
