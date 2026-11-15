"""SQLite access: connection factory, unit-of-work sessions and the migration runner."""

from __future__ import annotations

import importlib.util
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from zoo_platform.ports import ConnectionFactory

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def sqlite_factory(path: str) -> ConnectionFactory:
    def connect() -> sqlite3.Connection:
        conn = sqlite3.connect(path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    return connect


class Database:
    def __init__(self, connect: ConnectionFactory) -> None:
        self._connect = connect

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        """One unit of work: commit when the block succeeds, roll back when it raises."""
        conn = self._connect()
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def migrate(self, target: str | None = None) -> list[str]:
        """Apply pending migrations in name order, up to and including `target`.

        A migration is either `NNNN_name.sql` or `NNNN_name.py` exposing `upgrade(conn)`.
        """
        applied: list[str] = []
        with self.session() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(name TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
            )
            done = {row["name"] for row in conn.execute("SELECT name FROM schema_migrations")}
        for path in sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9][0-9]_*")):
            if path.suffix not in {".sql", ".py"} or path.stem in done:
                continue
            if target is not None and path.stem[:4] > target[:4]:
                break
            with self.session() as conn:
                if path.suffix == ".sql":
                    conn.executescript(path.read_text(encoding="utf-8"))
                else:
                    _load(path).upgrade(conn)
                conn.execute("INSERT INTO schema_migrations (name) VALUES (?)", (path.stem,))
            applied.append(path.stem)
        return applied


def _load(path: Path):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(f"zoo_platform_migration_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load migration {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
