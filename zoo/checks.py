"""Acceptance checks for the hard modes.

The tests run in a pytest subprocess, so the learner's project is always imported fresh and
a hanging test cannot freeze the game. Results are cached in
`.zoo/status-<mode>.json` under a fingerprint of the project and its tests: the game only
reruns the suite after a file changed.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, TypedDict

from zoo.modes import Mode, ModeLevel
from zoo.paths import ROOT, STATE_DIR

Outcome = Literal["pass", "fail", "skip"]
LevelStatus = Literal["healthy", "broken", "todo"]

SUITE_TIMEOUT_S = 300
FINGERPRINT_SUFFIXES = {".py", ".sql", ".json", ".toml"}
SKIPPED_DIRS = {"__pycache__", ".pytest_cache", "tickets", "architecture"}


class CheckResultDict(TypedDict):
    name: str
    outcome: Outcome
    message: str


class LevelReportDict(TypedDict):
    status: LevelStatus
    passed: int
    total: int
    results: list[CheckResultDict]


class Snapshot(TypedDict):
    """What the game knows about a mode's acceptance tests right now."""

    state: Literal["ready", "checking"]
    checked_at: float | None
    levels: dict[str, LevelReportDict] | None


class _CachedRun(TypedDict):
    fingerprint: str
    checked_at: float
    levels: dict[str, LevelReportDict]


class ResultsBoard(Protocol):
    def snapshot(self, mode: Mode) -> Snapshot: ...


@dataclass(frozen=True)
class CheckResult:
    name: str
    outcome: Outcome
    message: str


@dataclass(frozen=True)
class LevelReport:
    status: LevelStatus
    passed: int
    total: int
    results: tuple[CheckResult, ...]

    def to_dict(self) -> LevelReportDict:
        return {
            "status": self.status,
            "passed": self.passed,
            "total": self.total,
            "results": [
                {"name": result.name, "outcome": result.outcome, "message": result.message}
                for result in self.results
            ],
        }


def fingerprint(mode: Mode) -> str:
    digest = hashlib.sha256()
    for path in sorted(mode.root.rglob("*")):
        if not path.is_file() or path.suffix not in FINGERPRINT_SUFFIXES:
            continue
        if SKIPPED_DIRS.intersection(path.relative_to(mode.root).parts):
            continue
        stat = path.stat()
        digest.update(
            f"{path.relative_to(mode.root).as_posix()}:{stat.st_size}:{stat.st_mtime_ns};".encode()
        )
    return digest.hexdigest()


def _test_name(nodeid: str) -> str:
    return nodeid.split("::", 1)[-1].removeprefix("test_").replace("_", " ")


def _status(results: list[CheckResult], collection_failed: bool) -> LevelStatus:
    if collection_failed:
        return "broken"
    if results and all(result.outcome == "pass" for result in results):
        return "healthy"
    return "todo"


def _outcome(text: str) -> Outcome:
    """pytest_report writes pass, fail or skip; anything else counts as a failure."""
    if text == "pass":
        return "pass"
    return "skip" if text == "skip" else "fail"


def _report(raw: list[dict[str, str]]) -> LevelReport:
    if not raw:
        return LevelReport("broken", 0, 1, (CheckResult("suite", "fail", "no test ran"),))
    collection_failed = any("::" not in item["nodeid"] for item in raw)
    results = tuple(
        CheckResult(
            "collection" if "::" not in item["nodeid"] else _test_name(item["nodeid"]),
            _outcome(item["outcome"]),
            item["message"],
        )
        for item in raw
    )
    passed = sum(result.outcome == "pass" for result in results)
    return LevelReport(_status(list(results), collection_failed), passed, len(results), results)


def _whole_run_failed(levels: list[ModeLevel], message: str) -> dict[str, LevelReport]:
    failure = LevelReport("broken", 0, 1, (CheckResult("suite", "fail", message),))
    return {level.id: failure for level in levels}


def run_levels(mode: Mode, levels: list[ModeLevel]) -> dict[str, LevelReport]:
    """One pytest process for every requested level: importing the project once is faster
    than one process per level, and results are grouped back by test file."""
    with tempfile.TemporaryDirectory(prefix="zoo-check-") as scratch:
        report_path = Path(scratch) / "report.json"
        command = [
            sys.executable,
            "-m",
            "pytest",
            *(level.test for level in levels),
            "-q",
            # One ticket whose tests do not import must not hide the verdict of the others.
            "--continue-on-collection-errors",
            "-p",
            "no:cacheprovider",
            "-p",
            "zoo.pytest_report",
            f"--zoo-report={report_path}",
            "-W",
            "ignore",
        ]
        python_path = [str(ROOT), *filter(None, [os.environ.get("PYTHONPATH")])]
        env = {
            **os.environ,
            "PYTHONPATH": os.pathsep.join(python_path),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        try:
            completed = subprocess.run(
                command,
                cwd=mode.root,
                env=env,
                capture_output=True,
                text=True,
                timeout=SUITE_TIMEOUT_S,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return _whole_run_failed(levels, f"the tests ran for more than {SUITE_TIMEOUT_S}s")
        if not report_path.is_file():
            output = (completed.stderr or completed.stdout).strip().splitlines()
            return _whole_run_failed(levels, f"pytest did not run: {(output or ['?'])[-1]}")
        raw: list[dict[str, str]] = json.loads(report_path.read_text(encoding="utf-8"))

    by_file: dict[str, list[dict[str, str]]] = {level.test: [] for level in levels}
    for item in raw:
        path = item["nodeid"].split("::", 1)[0]
        if path in by_file:
            by_file[path].append(item)
    return {level.id: _report(by_file[level.test]) for level in levels}


class StatusBoard:
    """Serves the last known results at once and refreshes them in the background."""

    def __init__(self, state_dir: Path = STATE_DIR) -> None:
        self._state_dir = state_dir
        self._lock = threading.Lock()
        self._runs: dict[str, Future[None]] = {}
        self._latest: dict[str, _CachedRun] = {}
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="zoo-checks")

    def _cache_path(self, mode: Mode) -> Path:
        return self._state_dir / f"status-{mode.key}.json"

    def _read_cache(self, mode: Mode) -> _CachedRun | None:
        if mode.key in self._latest:
            return self._latest[mode.key]
        try:
            cached: _CachedRun = json.loads(self._cache_path(mode).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return cached

    def _write_cache(self, mode: Mode, payload: _CachedRun) -> None:
        """Results live in memory first; the file only lets them survive a restart."""
        self._latest[mode.key] = payload
        try:
            self._state_dir.mkdir(parents=True, exist_ok=True)
            target = self._cache_path(mode)
            partial = target.with_suffix(".tmp")
            partial.write_text(json.dumps(payload), encoding="utf-8")
            partial.replace(target)
        except OSError:
            return

    def _refresh(self, mode: Mode, current: str) -> None:
        reports = run_levels(mode, list(mode.levels))
        self._write_cache(
            mode,
            {
                "fingerprint": current,
                "checked_at": time.time(),
                "levels": {level_id: report.to_dict() for level_id, report in reports.items()},
            },
        )

    def snapshot(self, mode: Mode) -> Snapshot:
        current = fingerprint(mode)
        cached = self._read_cache(mode)
        fresh = cached is not None and cached["fingerprint"] == current
        with self._lock:
            running = self._runs.get(mode.key)
            if running is not None and running.done():
                running = None
                self._runs.pop(mode.key, None)
            if not fresh and running is None:
                self._runs[mode.key] = self._executor.submit(self._refresh, mode, current)
                running = self._runs[mode.key]
        return {
            "state": "ready" if fresh and running is None else "checking",
            "checked_at": cached["checked_at"] if cached else None,
            "levels": cached["levels"] if cached else None,
        }

    def wait(self, mode: Mode, timeout: float | None = None) -> None:
        with self._lock:
            running = self._runs.get(mode.key)
        if running is not None:
            running.result(timeout=timeout)
