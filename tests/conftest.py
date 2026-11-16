from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from zoo.checks import Snapshot
from zoo.modes import Mode, load_mode
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


def _tiny_mode(folder: Path, tests: list[str]) -> Mode:
    """A one-folder acceptance mode with one test file per level."""
    levels = []
    for number, body in enumerate(tests, start=1):
        name = f"test_{number:02d}.py"
        (folder / name).write_text(body, encoding="utf-8")
        levels.append(
            {
                "id": f"{number:02d}",
                "label": "L",
                "pattern": "P",
                "title": "T",
                "test": name,
                "ticket": name,
                "without": "naive",
                "with": "built",
            }
        )
    manifest = {
        "key": "tiny",
        "title": "Tiny",
        "tagline": "t",
        "runtime": "acceptance",
        "project": ".",
        "tests": ".",
        "levels": levels,
    }
    (folder / "zoo-mode.json").write_text(json.dumps(manifest), encoding="utf-8")
    return load_mode(folder)


@pytest.fixture
def tiny_mode() -> Callable[[Path, list[str]], Mode]:
    return _tiny_mode
