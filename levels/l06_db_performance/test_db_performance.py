import sqlite3
import threading
import time

import pytest

from levels.l06_db_performance.db_performance import (
    CATALOG_QUERY_SHAPE,
    SCHEMA,
    ConnectionPool,
    PoolExhausted,
    animals_with_enclosure,
    catalog_page,
    connect,
    explain,
    index_statements,
    seed,
)


@pytest.fixture
def conn() -> sqlite3.Connection:
    connection = connect()
    connection.executescript(SCHEMA)
    seed(connection, animals=600)
    return connection


class QueryCounter:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.statements: list[str] = []
        conn.set_trace_callback(self.statements.append)

    @property
    def selects(self) -> int:
        return sum(1 for s in self.statements if s.lstrip().upper().startswith("SELECT"))


def read_all_pages(conn: sqlite3.Connection, species: str, limit: int) -> list[int]:
    ids: list[int] = []
    cursor = None
    while True:
        page = catalog_page(conn, species, limit, cursor)
        ids.extend(item["id"] for item in page.items)
        if page.next_cursor is None:
            return ids
        cursor = page.next_cursor


def expected_ids(conn: sqlite3.Connection, species: str) -> list[int]:
    rows = conn.execute(
        "SELECT id FROM animals WHERE species = ? ORDER BY arrived_at DESC, id DESC", (species,)
    )
    return [row["id"] for row in rows]


def test_index_removes_scan_and_sort(conn: sqlite3.Connection) -> None:
    for statement in index_statements():
        conn.execute(statement)
    plan = " | ".join(explain(conn, CATALOG_QUERY_SHAPE, ("cat", 1_400, 99, 20)))
    assert "SCAN animals" not in plan, f"full table scan: {plan}"
    assert "TEMP B-TREE" not in plan, f"extra sort: {plan}"


def test_first_page_is_newest_first(conn: sqlite3.Connection) -> None:
    page = catalog_page(conn, "cat", 10)
    assert [item["id"] for item in page.items] == expected_ids(conn, "cat")[:10]
    assert set(page.items[0]) == {"id", "name", "arrived_at"}
    assert page.next_cursor is not None


def test_pages_cover_everything_once(conn: sqlite3.Connection) -> None:
    assert read_all_pages(conn, "fox", 7) == expected_ids(conn, "fox")


def test_last_page_has_no_cursor(conn: sqlite3.Connection) -> None:
    total = len(expected_ids(conn, "owl"))
    page = catalog_page(conn, "owl", total)
    assert len(page.items) == total
    assert page.next_cursor is None, "exactly `limit` rows left must still end the pagination"


def test_new_arrivals_do_not_duplicate_rows(conn: sqlite3.Connection) -> None:
    before = expected_ids(conn, "cat")
    first = catalog_page(conn, "cat", 10)
    conn.executemany(
        "INSERT INTO animals (name, species, enclosure_id, arrived_at) VALUES (?, 'cat', 1, ?)",
        [(f"newcomer-{i}", 9_000 + i) for i in range(5)],
    )
    second = catalog_page(conn, "cat", 10, first.next_cursor)
    seen = [item["id"] for item in first.items + second.items]
    assert seen == before[:20], "OFFSET pagination would serve page one's last rows again"


def test_cursor_query_does_not_use_offset(conn: sqlite3.Connection) -> None:
    counter = QueryCounter(conn)
    first = catalog_page(conn, "cat", 5)
    catalog_page(conn, "cat", 5, first.next_cursor)
    assert not any("OFFSET" in s.upper() for s in counter.statements)


def test_enclosures_load_in_one_query(conn: sqlite3.Connection) -> None:
    ids = list(range(1, 51))
    counter = QueryCounter(conn)
    rows = animals_with_enclosure(conn, ids)
    assert [row["id"] for row in rows] == ids
    assert all(row["enclosure"].startswith("Enclosure ") for row in rows)
    assert counter.selects == 1, f"N+1 detected: {counter.selects} queries for 50 animals"


def test_pool_reuses_connections() -> None:
    opened: list[object] = []

    def factory() -> object:
        opened.append(object())
        return opened[-1]

    pool = ConnectionPool(factory, size=2, timeout=0.1)
    for _ in range(5):
        with pool.connection() as first:
            pass
    with pool.connection() as again:
        assert again is first
    assert len(opened) == 1


def test_pool_never_exceeds_its_size() -> None:
    pool = ConnectionPool(object, size=3, timeout=2.0)
    active, peak, lock = 0, 0, threading.Lock()
    served: list[int] = []

    def borrow() -> None:
        nonlocal active, peak
        with pool.connection():
            served.append(1)
            with lock:
                active += 1
                peak = max(peak, active)
            time.sleep(0.01)
            with lock:
                active -= 1

    threads = [threading.Thread(target=borrow) for _ in range(12)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(served) == 12, "every borrower must get a connection"
    assert 1 <= pool.created <= 3 and peak <= 3


def test_pool_times_out_when_exhausted() -> None:
    pool = ConnectionPool(object, size=1, timeout=0.05)
    with pool.connection(), pytest.raises(PoolExhausted), pool.connection():
        pass


def test_pool_gets_connection_back_after_error() -> None:
    pool = ConnectionPool(object, size=1, timeout=0.05)
    with pytest.raises(RuntimeError), pool.connection():
        raise RuntimeError("query failed")
    with pool.connection():
        pass
