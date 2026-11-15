"""A pytest plugin that writes every test outcome to a JSON file.

Loaded in a subprocess with `-p zoo.pytest_report --zoo-report=<path>`, so the learner's
project is imported in a fresh interpreter each time and the game never runs stale code.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--zoo-report", action="store", default=None, help="where to write results")


def _first_line(report: pytest.TestReport | pytest.CollectReport) -> str:
    crash = getattr(report.longrepr, "reprcrash", None)
    message = crash.message if crash is not None else str(report.longrepr or "")
    message = message.strip()
    return message.splitlines()[0] if message else "failed"


class JsonReport:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.results: list[dict[str, str]] = []

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if report.when != "call" and not report.failed:
            return
        outcome = "pass" if report.passed else "fail"
        if report.skipped:
            outcome = "skip"
        self.results.append(
            {
                "nodeid": report.nodeid.replace("\\", "/"),
                "outcome": outcome,
                "message": "" if report.passed else _first_line(report),
            }
        )

    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        if report.failed:
            self.results.append(
                {
                    "nodeid": report.nodeid.replace("\\", "/"),
                    "outcome": "fail",
                    "message": _first_line(report),
                }
            )

    def pytest_sessionfinish(self, session: pytest.Session) -> None:
        self.path.write_text(json.dumps(self.results), encoding="utf-8")


def pytest_configure(config: pytest.Config) -> None:
    target = config.getoption("--zoo-report")
    if target:
        config.pluginmanager.register(JsonReport(Path(target)), "zoo-json-report")
