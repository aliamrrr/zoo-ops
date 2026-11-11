import sqlite3

import pytest

from levels.l04_idempotency.idempotency import (
    IdempotencyConflict,
    IdempotencyStore,
    RequestInProgress,
    StoredResponse,
    belly,
    connect,
    fingerprint,
    record_meal,
)


@pytest.fixture
def conn() -> sqlite3.Connection:
    return connect()


class CountingHandler:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> StoredResponse:
        self.calls += 1
        return StoredResponse(201, {"meal": self.calls})


def test_fingerprint_ignores_key_order() -> None:
    assert fingerprint({"cat": "miso", "grams": 50}) == fingerprint({"grams": 50, "cat": "miso"})
    assert fingerprint({"cat": "miso", "grams": 50}) != fingerprint({"cat": "miso", "grams": 51})
    assert len(fingerprint({})) == 64


def test_same_key_runs_the_handler_once(conn: sqlite3.Connection) -> None:
    store, handler = IdempotencyStore(conn), CountingHandler()
    first = store.execute("key-1", {"cat": "miso"}, handler)
    second = store.execute("key-1", {"cat": "miso"}, handler)
    assert handler.calls == 1
    assert first == StoredResponse(201, {"meal": 1})
    assert second == StoredResponse(201, {"meal": 1}, replayed=True)


def test_different_keys_are_independent(conn: sqlite3.Connection) -> None:
    store, handler = IdempotencyStore(conn), CountingHandler()
    store.execute("key-1", {"cat": "miso"}, handler)
    store.execute("key-2", {"cat": "miso"}, handler)
    assert handler.calls == 2


def test_reused_key_with_other_payload_is_rejected(conn: sqlite3.Connection) -> None:
    store, handler = IdempotencyStore(conn), CountingHandler()
    store.execute("key-1", {"cat": "miso", "grams": 50}, handler)
    with pytest.raises(IdempotencyConflict):
        store.execute("key-1", {"cat": "miso", "grams": 500}, handler)
    assert handler.calls == 1


def test_key_still_in_progress_is_rejected(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT INTO idempotency_keys (key, request_hash, status) VALUES (?, ?, 'in_progress')",
        ("key-1", fingerprint({"cat": "miso"})),
    )
    with pytest.raises(RequestInProgress):
        IdempotencyStore(conn).execute("key-1", {"cat": "miso"}, CountingHandler())


def test_failed_handler_releases_the_key(conn: sqlite3.Connection) -> None:
    store = IdempotencyStore(conn)

    def crash() -> StoredResponse:
        raise ConnectionError("kitchen on fire")

    with pytest.raises(ConnectionError):
        store.execute("key-1", {"cat": "miso"}, crash)
    handler = CountingHandler()
    assert store.execute("key-1", {"cat": "miso"}, handler).status_code == 201
    assert handler.calls == 1, "a failure must not lock the key forever"


def test_response_is_persisted(conn: sqlite3.Connection) -> None:
    IdempotencyStore(conn).execute("key-1", {"cat": "miso"}, CountingHandler())
    replay = IdempotencyStore(conn).execute("key-1", {"cat": "miso"}, CountingHandler())
    assert replay.replayed and replay.body == {"meal": 1}, "replays must survive a new store"


def test_record_meal_is_idempotent_on_order_id(conn: sqlite3.Connection) -> None:
    assert record_meal(conn, "order-1", "miso", 50) is True
    assert record_meal(conn, "order-1", "miso", 50) is False
    assert belly(conn, "miso") == 50
    assert conn.execute("SELECT COUNT(*) FROM meals").fetchone()[0] == 1


def test_record_meal_accumulates_distinct_orders(conn: sqlite3.Connection) -> None:
    record_meal(conn, "order-1", "miso", 50)
    record_meal(conn, "order-2", "miso", 30)
    record_meal(conn, "order-3", "tofu", 20)
    assert belly(conn, "miso") == 80
    assert belly(conn, "tofu") == 20


def test_record_meal_is_atomic(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE bellies")
    conn.execute(
        "CREATE TABLE bellies (cat TEXT PRIMARY KEY, grams_eaten INTEGER NOT NULL "
        "CHECK (grams_eaten < 100))"
    )
    record_meal(conn, "order-1", "miso", 60)
    with pytest.raises(sqlite3.IntegrityError):
        record_meal(conn, "order-2", "miso", 60)
    assert (
        conn.execute("SELECT COUNT(*) FROM meals").fetchone()[0] == 1
    ), "the meal insert must roll back when the belly update fails"
