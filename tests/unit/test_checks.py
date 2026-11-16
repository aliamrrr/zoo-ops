"""Acceptance checks run a real pytest subprocess on a tiny mode built for the test."""

from __future__ import annotations

import json
import os
from pathlib import Path

from zoo.checks import LevelReportDict, Snapshot, StatusBoard, fingerprint, run_levels
from zoo.modes import Mode, find_mode, load_mode
from zoo.runtimes import AcceptanceRuntime

PASSING = "def test_it_works():\n    assert 1 + 1 == 2\n"
FAILING = "def test_it_works():\n    assert 1 + 1 == 3, 'math is broken'\n"
BROKEN = "def test_it_works(:\n"


def tiny_mode(folder: Path, tests: list[str]) -> Mode:
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


def test_each_level_gets_its_own_verdict(tmp_path: Path) -> None:
    mode = tiny_mode(tmp_path, [PASSING, FAILING, BROKEN])
    reports = run_levels(mode, list(mode.levels))
    assert reports["01"].status == "healthy"
    assert reports["01"].passed == reports["01"].total == 1
    assert reports["02"].status == "todo"
    assert "math is broken" in reports["02"].results[0].message
    assert reports["03"].status == "broken"


def test_the_fingerprint_follows_the_files(tmp_path: Path) -> None:
    mode = tiny_mode(tmp_path, [PASSING])
    before = fingerprint(mode)
    assert fingerprint(mode) == before
    target = tmp_path / "test_01.py"
    target.write_text(FAILING, encoding="utf-8")
    os.utime(target, ns=(1, 1))
    assert fingerprint(mode) != before


def test_the_board_serves_the_cache_and_refreshes_in_the_background(tmp_path: Path) -> None:
    project, state = tmp_path / "project", tmp_path / "state"
    project.mkdir()
    mode = tiny_mode(project, [PASSING])
    board = StatusBoard(state)
    first: Snapshot = board.snapshot(mode)
    assert first["state"] == "checking"
    board.wait(mode, timeout=120)
    ready = board.snapshot(mode)
    assert ready["state"] == "ready"
    assert ready["levels"] is not None and ready["levels"]["01"]["status"] == "healthy"
    # A restarted game reads the results back from disk instead of running the suite again.
    assert StatusBoard(state).snapshot(mode)["state"] == "ready"


class GreenBoard:
    def snapshot(self, mode: Mode) -> Snapshot:
        level: LevelReportDict = {
            "status": "healthy",
            "passed": 1,
            "total": 1,
            "results": [{"name": "it works", "outcome": "pass", "message": ""}],
        }
        return {"state": "ready", "checked_at": 0.0, "levels": {"01": level}}


def test_green_tests_ship_only_once_the_block_is_placed(tmp_path: Path) -> None:
    runtime = AcceptanceRuntime(find_mode("hard"), GreenBoard(), tmp_path)
    entry = runtime.systems()["01"]
    assert entry["status"] == "todo"
    assert "Place block 01" in str(entry["headline"])

    answer = json.loads(find_mode("hard").blueprint_path.read_text(encoding="utf-8"))["answers"]
    placement = {"slot": answer["01"]["slots"][0], "links": answer["01"]["links"]}
    runtime.blueprint().save({"01": placement})
    assert runtime.systems()["01"]["status"] == "healthy"
    assert "01" in runtime.backend.online
