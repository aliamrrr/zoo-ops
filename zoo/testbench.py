"""Runs pytest in-process, collects every result, and renders a pixel-art scoreboard."""

from __future__ import annotations

import contextlib
import io
from collections import defaultdict
from dataclasses import dataclass
from typing import Literal

import pytest
from rich.console import Console, Group
from rich.padding import Padding
from rich.table import Table
from rich.text import Text

from zoo.registry import LEVELS, ROOT, Level
from zoo.sprites import gradient_strip, palette, sprite_text

Outcome = Literal["pass", "fail", "todo"]
LevelStatus = Literal["healthy", "broken", "todo"]

GREEN = "#2FBF71"
RED = "#D64545"
AMBER = "#E3A03A"
INK = "#1E1E1E"

BADGES: dict[Outcome, tuple[str, str]] = {
    "pass": (" PASS ", f"bold {INK} on {GREEN}"),
    "fail": (" FAIL ", f"bold white on {RED}"),
    "todo": (" TODO ", f"bold {INK} on {AMBER}"),
}
STATUS_LABELS: dict[LevelStatus, tuple[str, str]] = {
    "healthy": (" ONLINE ", f"bold {INK} on {GREEN}"),
    "broken": (" ON FIRE ", f"bold white on {RED}"),
    "todo": (" UNDER CONSTRUCTION ", f"bold {INK} on {AMBER}"),
}


@dataclass(frozen=True)
class TestResult:
    name: str
    outcome: Outcome
    message: str


class ResultCollector:
    """A pytest plugin object: pytest calls these hooks while it runs."""

    def __init__(self) -> None:
        self.by_level: dict[str, list[TestResult]] = defaultdict(list)

    @staticmethod
    def _level_slug(nodeid: str) -> str:
        parts = nodeid.replace("\\", "/").split("/")
        return parts[1] if len(parts) > 1 and parts[0] == "levels" else "?"

    @staticmethod
    def _crash_message(report: pytest.TestReport | pytest.CollectReport) -> str:
        crash = getattr(report.longrepr, "reprcrash", None)
        message = crash.message if crash is not None else str(report.longrepr)
        return message.strip().splitlines()[0] if message.strip() else "failed"

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        is_call = report.when == "call"
        if not (is_call or report.failed):
            return
        name = report.nodeid.split("::", 1)[-1].removeprefix("test_").replace("_", " ")
        if report.passed:
            self._add(report.nodeid, TestResult(name, "pass", ""))
            return
        message = self._crash_message(report)
        if message.startswith("NotImplementedError"):
            todo = message.partition(":")[2].strip() or "a TODO"
            self._add(report.nodeid, TestResult(name, "todo", f"needs {todo}"))
        else:
            self._add(report.nodeid, TestResult(name, "fail", message))

    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        if report.failed:
            self._add(report.nodeid, TestResult("collection", "fail", self._crash_message(report)))

    def _add(self, nodeid: str, result: TestResult) -> None:
        self.by_level[self._level_slug(nodeid)].append(result)


def run_tests(levels: list[Level]) -> ResultCollector:
    collector = ResultCollector()
    args = [str(level.folder) for level in levels]
    args += ["-p", "no:cacheprovider", "-q", "--rootdir", str(ROOT), "-W", "ignore"]
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        pytest.main(args, plugins=[collector])
    return collector


def level_status(results: list[TestResult]) -> LevelStatus:
    if results and all(result.outcome == "pass" for result in results):
        return "healthy"
    if any(result.outcome == "fail" for result in results):
        return "broken"
    return "todo"


def progress_bar(done: int, total: int, width: int = 24) -> Text:
    filled = round(width * done / total) if total else 0
    bar = Text(no_wrap=True)
    colors = palette()
    ramp = [colors[key] for key in ("D", "G", "y", "p", "B")]
    for i in range(width):
        if i < filled:
            bar.append("█", style=ramp[i * len(ramp) // width])
        else:
            bar.append("░", style="grey35")
    bar.append(f"  {done}/{total}", style="bold")
    return bar


def badge_line(outcome: Outcome, text: str, note: str = "") -> Text:
    badge, badge_style = BADGES[outcome]
    return Text.assemble((badge, badge_style), " ", text, (f"  {note}" if note else "", "grey50"))


def message_line(message: str) -> Text:
    return Text(f"       {message}", style="grey62", overflow="ellipsis", no_wrap=True)


def detail_lines(results: list[TestResult]) -> list[Text]:
    lines = []
    for result in results:
        lines.append(badge_line(result.outcome, result.name))
        if result.message:
            lines.append(message_line(result.message))
    return lines


def summary_lines(results: list[TestResult], level: Level, max_failures: int = 3) -> list[Text]:
    """Real failures one by one, missing TODOs grouped by function."""
    lines = []
    failures = [result for result in results if result.outcome == "fail"]
    for result in failures[:max_failures]:
        lines.append(badge_line("fail", result.name))
        lines.append(message_line(result.message))
    if len(failures) > max_failures:
        lines.append(
            message_line(
                f"... {len(failures) - max_failures} more failures, run: "
                f"python -m zoo test {level.number}"
            )
        )
    waiting: dict[str, int] = defaultdict(int)
    for result in results:
        if result.outcome == "todo":
            waiting[result.message.removeprefix("needs ")] += 1
    for todo, count in waiting.items():
        lines.append(badge_line("todo", todo, f"blocks {count} test{'s' if count > 1 else ''}"))
    return lines


def render_level(level: Level, results: list[TestResult], verbose: bool) -> Table:
    status = level_status(results)
    label, label_style = STATUS_LABELS[status]
    passed = sum(result.outcome == "pass" for result in results)

    title = Text.assemble(
        (f"{level.id} ", "bold grey50"),
        (level.pattern.upper(), "bold"),
        ("   ", ""),
        (label, label_style),
    )
    subtitle = Text(
        f"{level.station}  /  {level.keeper}  /  levels/{level.slug}/{level.todo_file}",
        style="grey50",
    )
    lines: list[Text] = [title, subtitle, progress_bar(passed, len(results))]

    lines.extend(detail_lines(results) if verbose else summary_lines(results, level))

    grid = Table.grid(padding=(0, 3))
    grid.add_column(width=12, no_wrap=True)
    grid.add_column(ratio=1)
    grid.add_row(sprite_text(level.animal), Group(*lines))
    return grid


def render_scoreboard(console: Console, statuses: list[LevelStatus], total: int) -> None:
    online = statuses.count("healthy")
    colors = {"healthy": GREEN, "broken": RED, "todo": AMBER}
    squares = Text(no_wrap=True)
    for status in statuses:
        squares.append("██", style=colors[status])
        squares.append(" ")
    message = (
        "Every station is online. The zoo runs itself. Ship it."
        if online == total
        else "Fix a station, then run the bench again. The game shows what breaks: "
        "python -m zoo play"
    )
    console.print(
        Padding(
            Text.assemble(
                ("STATIONS ONLINE  ", "bold"), (f"{online}/{total}   ", f"bold {GREEN}"), squares
            ),
            (0, 2),
        )
    )
    console.print(Padding(Text(message, style="grey62"), (0, 2)))


def bench(levels: list[Level], verbose: bool) -> int:
    console = Console(highlight=False)
    width = min(console.width, 100)
    console.print(gradient_strip(width))
    console.print(Padding(Text.assemble(("ZOO OPS", "bold"), ("  test bench", "grey50")), (0, 2)))
    console.print()

    with console.status("[grey62]The keepers are running the tests...", spinner="dots"):
        collector = run_tests(levels)

    statuses: list[LevelStatus] = []
    for level in levels:
        results = collector.by_level.get(level.slug, [])
        statuses.append(level_status(results))
        console.print(Padding(render_level(level, results, verbose or len(levels) == 1), (0, 2)))
        console.print()

    if len(levels) == len(LEVELS):
        render_scoreboard(console, statuses, len(LEVELS))
    console.print(gradient_strip(width))
    return 0 if all(status == "healthy" for status in statuses) else 1
