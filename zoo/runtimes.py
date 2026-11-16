"""How a mode is played. The server and the CLI only talk to a `ModeRuntime`; the manifest's
`runtime` field picks the implementation, so no caller ever asks which mode it is in.

- `ClassicRuntime`: the learner's level files run live, on every click, and their scenes
  decide which keepers are awake.
- `AcceptanceRuntime` (Hard, Hard++): the learner's project is a real codebase checked by
  acceptance tests in a subprocess; the game plays each ticket that passes them and whose
  block sits at the right place of the architecture blueprint.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol

from zoo.blueprint import Blueprint
from zoo.checks import LevelReportDict, ResultsBoard
from zoo.game import GameBackend, SimulatedBackend
from zoo.kit import SceneResult
from zoo.modes import Mode, ModeLevel, all_modes
from zoo.paths import STATE_DIR
from zoo.registry import LEVELS, Level, find_level, level_module, play_level
from zoo.testbench import bench, hard_bench

SseFormatter = Callable[..., str]
SystemsReport = dict[str, dict[str, object]]


class UsageError(Exception):
    """A command that does not apply to this mode, with the one that does."""


class NoBlueprint(LookupError):
    pass


def format_sse(data: str, event: str | None = None, event_id: str | None = None) -> str:
    """The reference Server-Sent Events encoder, used once a hard mode ships its async ticket."""
    lines = [f"id: {event_id}"] if event_id is not None else []
    if event is not None:
        lines.append(f"event: {event}")
    lines += [f"data: {line}" for line in data.split("\n")]
    return "\n".join(lines) + "\n\n"


class ModeRuntime(Protocol):
    mode: Mode

    @property
    def backend(self) -> GameBackend | SimulatedBackend:
        """The kiosk and food bowls the live game calls."""
        ...

    def public_levels(self) -> list[dict[str, object]]: ...

    def systems(self) -> SystemsReport:
        """The state of the ten keepers: what the game should show as built."""
        ...

    def stream_formatter(self) -> SseFormatter | None:
        """How the Owl streams its answers, or None while async processing is not built."""
        ...

    def blueprint(self) -> Blueprint: ...

    def bench(self, keys: Sequence[str], verbose: bool) -> int: ...

    def scenes(self, keys: Sequence[str]) -> list[tuple[Level, SceneResult]]: ...

    def reset_paths(self, keys: Sequence[str], whole_project: bool) -> list[str]:
        """The files `zoo reset` restores, relative to the repository."""
        ...


class ClassicRuntime:
    def __init__(self, mode: Mode, state_dir: Path = STATE_DIR) -> None:
        self.mode = mode
        self._backend = GameBackend()

    @property
    def backend(self) -> GameBackend:
        return self._backend

    def public_levels(self) -> list[dict[str, object]]:
        return [level.to_public_dict() for level in LEVELS]

    def play(self, key: str) -> dict[str, object]:
        """Replay one level's scene, for its station."""
        level = find_level(key)
        result = play_level(level).to_dict()
        result["todos_left"] = level.todos_left()
        return result

    def systems(self) -> SystemsReport:
        """The morning check: every scene runs once, the game adapts to what works."""
        report: SystemsReport = {}
        for level in LEVELS:
            result = play_level(level)
            report[level.id] = {
                "status": result.status,
                "headline": result.headline,
                "metrics": result.metrics,
            }
        return report

    def stream_formatter(self) -> SseFormatter | None:
        """The learner's sse_event from level 08, or None while it is a TODO or does not load."""
        try:
            sse_event: SseFormatter = level_module("l08_async.async_jobs").sse_event
            sse_event("probe")
        except Exception:  # noqa: BLE001 - NotImplementedError, or a file that does not import
            return None
        return sse_event

    def blueprint(self) -> Blueprint:
        raise NoBlueprint(f"{self.mode.title} has no blueprint")

    def bench(self, keys: Sequence[str], verbose: bool) -> int:
        return bench(self._levels(keys), verbose=verbose)

    def scenes(self, keys: Sequence[str]) -> list[tuple[Level, SceneResult]]:
        return [(level, play_level(level)) for level in self._levels(keys)]

    def reset_paths(self, keys: Sequence[str], whole_project: bool) -> list[str]:
        if whole_project:
            return [self.mode.project_label]
        if not keys:
            raise UsageError("name the levels to reset, e.g. zoo reset 3 (or --project for all)")
        return [level.relative_todo_path for level in self._levels(keys)]

    @staticmethod
    def _levels(keys: Sequence[str]) -> list[Level]:
        return [find_level(key) for key in keys] if keys else list(LEVELS)


class AcceptanceRuntime:
    def __init__(self, mode: Mode, board: ResultsBoard, state_dir: Path = STATE_DIR) -> None:
        self.mode = mode
        self._board = board
        self._state_dir = state_dir
        self._backend = SimulatedBackend()

    @property
    def backend(self) -> SimulatedBackend:
        self.systems()
        return self._backend

    def public_levels(self) -> list[dict[str, object]]:
        return [
            {
                "id": level.id,
                "number": level.number,
                "label": level.label,
                "pattern": level.pattern,
                "title": level.title,
                "ticket": level.ticket,
                "ticket_text": (self.mode.root / str(level.ticket)).read_text(encoding="utf-8"),
                "test": level.test,
                "without": level.without,
                "with": level.with_,
            }
            for level in self.mode.levels
        ]

    def systems(self) -> SystemsReport:
        snapshot = self._board.snapshot(self.mode)
        checking = snapshot["state"] == "checking"
        reports = snapshot["levels"] or {}
        placed = self.blueprint().placed()
        report = {
            level.id: self._entry(level, reports.get(level.id), level.id in placed, checking)
            for level in self.mode.levels
        }
        self._backend.online = frozenset(
            level_id for level_id, entry in report.items() if entry["status"] == "healthy"
        )
        return report

    @staticmethod
    def _entry(
        level: ModeLevel, found: LevelReportDict | None, placed: bool, checking: bool
    ) -> dict[str, object]:
        """A ticket is in production when its acceptance tests pass and its block sits at the
        right place of the architecture blueprint."""
        if found is None:
            return {
                "status": "checking",
                "headline": "Running the acceptance tests...",
                "metrics": {},
                "checking": True,
                "results": [],
                "placed": placed,
                "tests_pass": False,
            }
        tests_pass = found["status"] == "healthy"
        failing = [item for item in found["results"] if item["outcome"] != "pass"]
        if tests_pass and placed:
            status, headline = "healthy", level.with_
        elif tests_pass:
            status = "todo"
            headline = f"Every test passes. Place block {level.id} on the Blueprint to ship it."
        else:
            status = found["status"]
            first = failing[0] if failing else None
            headline = f"{first['name']}: {first['message']}" if first else level.without
        return {
            "status": status,
            "headline": headline,
            "metrics": {
                "acceptance tests": f"{found['passed']}/{found['total']}",
                "blueprint": "placed" if placed else "not placed",
            },
            "checking": checking,
            "results": found["results"],
            "placed": placed,
            "tests_pass": tests_pass,
        }

    def stream_formatter(self) -> SseFormatter | None:
        return format_sse if "08" in self._backend.online else None

    def blueprint(self) -> Blueprint:
        return Blueprint(self.mode, self._state_dir)

    def bench(self, keys: Sequence[str], verbose: bool) -> int:
        return hard_bench(self.mode, self._levels(keys), self.blueprint(), verbose=verbose)

    def scenes(self, keys: Sequence[str]) -> list[tuple[Level, SceneResult]]:
        raise UsageError(
            f"scenes are Classic stories, {self.mode.title} has acceptance tests instead: "
            f"zoo test --mode {self.mode.key}"
        )

    def reset_paths(self, keys: Sequence[str], whole_project: bool) -> list[str]:
        if not whole_project:
            raise UsageError(
                f"A {self.mode.title} ticket touches many files, so the whole project is reset "
                f"at once.\nThis discards every change in {self.mode.project_label}:\n"
                f"  zoo reset --mode {self.mode.key} --project"
            )
        return [self.mode.project_label]

    def _levels(self, keys: Sequence[str]) -> list[ModeLevel]:
        return [self.mode.find_level(key) for key in keys] if keys else list(self.mode.levels)


def build_runtimes(board: ResultsBoard, state_dir: Path = STATE_DIR) -> dict[str, ModeRuntime]:
    runtimes: dict[str, ModeRuntime] = {}
    for key, mode in all_modes().items():
        if mode.runtime == "classic":
            runtimes[key] = ClassicRuntime(mode, state_dir)
        else:
            runtimes[key] = AcceptanceRuntime(mode, board, state_dir)
    return runtimes
