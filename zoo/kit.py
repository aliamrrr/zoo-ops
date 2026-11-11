"""Building blocks shared by every level: a controllable clock and the scene recorder."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Literal

Status = Literal["healthy", "broken", "todo"]
Tone = Literal["info", "good", "bad"]


class FakeClock:
    """A clock that only moves when told to. Tests and scenes stay deterministic and instant."""

    def __init__(self, start: float = 1_000.0) -> None:
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("time only moves forward")
        self._now += seconds

    def sleep(self, seconds: float) -> None:
        self.advance(seconds)


@dataclass(frozen=True)
class Event:
    tone: Tone
    text: str


@dataclass
class SceneResult:
    level: str
    status: Status
    headline: str
    events: list[Event] = field(default_factory=list)
    metrics: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class Scene:
    """Collects the story of one scene. Every `bad` line marks the station as broken."""

    def __init__(self) -> None:
        self.events: list[Event] = []
        self.metrics: dict[str, str] = {}
        self.failures: list[str] = []

    def info(self, text: str) -> None:
        self.events.append(Event("info", text))

    def good(self, text: str) -> None:
        self.events.append(Event("good", text))

    def bad(self, text: str) -> None:
        self.events.append(Event("bad", text))
        self.failures.append(text)

    def check(self, condition: bool, ok: str, ko: str) -> bool:
        if condition:
            self.good(ok)
        else:
            self.bad(ko)
        return condition

    def metric(self, name: str, value: object) -> None:
        self.metrics[name] = str(value)


def run_scene(
    level_id: str,
    play: Callable[[Scene], None],
    victory: str,
    timeout: float = 15.0,
) -> SceneResult:
    """Run a scene in a worker thread so a deadlock in learner code cannot freeze the game."""
    scene = Scene()
    outcome: dict[str, BaseException] = {}

    def target() -> None:
        try:
            play(scene)
        except BaseException as exc:  # noqa: BLE001 - every failure must reach the player
            outcome["error"] = exc

    worker = threading.Thread(target=target, name=f"scene-{level_id}", daemon=True)
    worker.start()
    worker.join(timeout)

    if worker.is_alive():
        scene.bad(f"The scene did not finish within {timeout:.0f}s. Deadlock or endless loop?")
        return SceneResult(level_id, "broken", scene.failures[0], scene.events, scene.metrics)

    error = outcome.get("error")
    if isinstance(error, NotImplementedError):
        missing = str(error) or "a TODO"
        scene.info(f"Under construction: {missing} is not implemented yet.")
        return SceneResult(
            level_id, "todo", f"Under construction: {missing}", scene.events, scene.metrics
        )
    if error is not None:
        scene.bad(f"Crash: {type(error).__name__}: {error}")

    if scene.failures:
        return SceneResult(level_id, "broken", scene.failures[0], scene.events, scene.metrics)
    return SceneResult(level_id, "healthy", victory, scene.events, scene.metrics)
