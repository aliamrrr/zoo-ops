"""The ten Classic levels, read from `levels/zoo-mode.json`: their files, TODOs and scenes."""

from __future__ import annotations

import importlib
import re
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from zoo.cast import KEEPERS
from zoo.kit import Event, SceneResult, run_scene
from zoo.modes import CLASSIC, ModeLevel, find_mode
from zoo.paths import ROOT, make_levels_importable

_TODO_PATTERN = re.compile(r'raise NotImplementedError\("([^"]+)"\)')


@dataclass(frozen=True)
class Level:
    number: int
    slug: str
    pattern: str
    station: str
    keeper: str
    animal: str
    pitch: str
    todo_file: str
    todos: tuple[str, ...]
    naive: tuple[str, ...]
    victory: str

    @classmethod
    def from_manifest(cls, spec: ModeLevel) -> Level:
        assert spec.exercise is not None, "the Classic manifest is validated on load"
        keeper = KEEPERS[spec.id]
        return cls(
            number=spec.number,
            slug=spec.test,
            pattern=spec.pattern,
            station=spec.title,
            keeper=keeper.name,
            animal=keeper.animal,
            pitch=spec.without,
            todo_file=spec.exercise.file,
            todos=spec.exercise.todos,
            naive=spec.exercise.naive,
            victory=spec.with_,
        )

    @property
    def id(self) -> str:
        return f"{self.number:02d}"

    @property
    def folder(self) -> Path:
        return find_mode(CLASSIC).root / self.slug

    @property
    def todo_path(self) -> Path:
        return self.folder / self.todo_file

    @property
    def relative_todo_path(self) -> str:
        return self.todo_path.relative_to(ROOT).as_posix()

    def todos_left(self) -> list[str]:
        """Names still raising NotImplementedError in the learner file."""
        try:
            source = self.todo_path.read_text(encoding="utf-8")
        except OSError:
            return list(self.todos)
        return _TODO_PATTERN.findall(source)

    def to_public_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "number": self.number,
            "slug": self.slug,
            "pattern": self.pattern,
            "station": self.station,
            "keeper": self.keeper,
            "animal": self.animal,
            "pitch": self.pitch,
            "file": self.relative_todo_path,
            "todos": list(self.todos),
            "todos_left": self.todos_left(),
        }


LEVELS: tuple[Level, ...] = tuple(Level.from_manifest(spec) for spec in find_mode(CLASSIC).levels)


def find_level(key: str | int) -> Level:
    """Accept 3, "3", "03" or "l03_reliability"."""
    text = str(key).strip().lower()
    for level in LEVELS:
        if text in {level.id, str(level.number), level.slug}:
            return level
    raise KeyError(f"unknown level {key!r}, expected 1 to {len(LEVELS)}")


def level_module(name: str) -> ModuleType:
    """Import `levels.<name>`: the learner's own code, fresh from the repository."""
    make_levels_importable()
    return importlib.import_module(f"levels.{name}")


def play_level(level: Level) -> SceneResult:
    try:
        module = level_module(f"{level.slug}.scene")
    except Exception as exc:  # noqa: BLE001 - a typo in a level must not take the game down
        headline = f"{level.todo_file} does not load: {type(exc).__name__}: {exc}"
        return SceneResult(level.id, "broken", headline, [Event("bad", headline)], {})
    return run_scene(level.id, module.play, level.victory)
