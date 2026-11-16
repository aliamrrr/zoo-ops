from __future__ import annotations

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from zoo.checks import Snapshot
from zoo.modes import Mode
from zoo.server import create_app


class FrozenBoard:
    """Acceptance results without running the suites: every ticket has one failing test."""

    def snapshot(self, mode: Mode) -> Snapshot:
        return {
            "state": "ready",
            "checked_at": 0.0,
            "levels": {
                level.id: {
                    "status": "todo",
                    "passed": 0,
                    "total": 1,
                    "results": [{"name": "it works", "outcome": "fail", "message": "not yet"}],
                }
                for level in mode.levels
            },
        }


@pytest.fixture
def make_client(tmp_path_factory: pytest.TempPathFactory) -> Callable[[], TestClient]:
    """A fresh app with its own state folder, each time it is called."""
    return lambda: TestClient(
        create_app(state_dir=tmp_path_factory.mktemp("state"), board=FrozenBoard())
    )


@pytest.fixture
def client(make_client: Callable[[], TestClient]) -> TestClient:
    return make_client()
