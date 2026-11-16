"""The three ways to play. Each mode is a folder with a `zoo-mode.json` manifest:

- `levels/`  Classic: ten guided levels, one file with TODOs each
- `hard/`    Hard: a real service, ten tickets, acceptance tests and an architecture blueprint
- `hardpp/`  Hard++: a distributed system in a deterministic simulation, same shape as Hard

Manifests are validated when they load, so a broken one stops the game at start-up with a
clear message instead of failing in the middle of a shift.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from zoo.paths import MODE_FOLDERS, ROOT

CLASSIC = "classic"
MANIFEST = "zoo-mode.json"
Runtime = Literal["classic", "acceptance"]


class Exercise(BaseModel):
    """A Classic level: the file the learner edits and the functions to write.

    `naive` lists the TODOs that already work in the starter, the slow way the pattern exists
    to fix (an N+1 query), instead of raising NotImplementedError.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    file: str
    todos: tuple[str, ...]
    naive: tuple[str, ...] = ()


class ModeLevel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    id: str = Field(pattern=r"^\d{2}$")
    label: str
    pattern: str
    title: str
    test: str
    without: str
    with_: str = Field(alias="with")
    ticket: str | None = None
    exercise: Exercise | None = None

    @property
    def number(self) -> int:
        return int(self.id)

    def summary(self) -> dict[str, object]:
        return {
            "id": self.id,
            "label": self.label,
            "pattern": self.pattern,
            "title": self.title,
            "without": self.without,
            "with": self.with_,
        }


class Mode(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str = Field(pattern=r"^[a-z]{2,12}$")
    title: str
    tagline: str
    runtime: Runtime
    root: Path
    project: str
    tests: str
    levels: tuple[ModeLevel, ...]

    @model_validator(mode="after")
    def _levels_fit_the_runtime(self) -> Mode:
        expected = [f"{number:02d}" for number in range(1, len(self.levels) + 1)]
        if [level.id for level in self.levels] != expected:
            raise ValueError("level ids must run from 01 in order")
        for level in self.levels:
            if self.runtime == "classic" and level.exercise is None:
                raise ValueError(f"Classic level {level.id} needs an exercise")
            if self.runtime == "acceptance" and level.ticket is None:
                raise ValueError(f"level {level.id} needs a ticket")
        return self

    @property
    def project_path(self) -> Path:
        return (self.root / self.project).resolve()

    @property
    def project_label(self) -> str:
        """The learner's project as shown to them, relative to the repository."""
        return self.project_path.relative_to(ROOT).as_posix()

    @property
    def blueprint_path(self) -> Path:
        return self.root / "architecture" / "blueprint.json"

    @property
    def has_blueprint(self) -> bool:
        return self.blueprint_path.is_file()

    def find_level(self, key: str | int) -> ModeLevel:
        text = str(key).strip().lower()
        for level in self.levels:
            if text in {level.id, str(level.number), level.test}:
                return level
        raise KeyError(f"unknown level {key!r} in {self.title}, expected 1 to {len(self.levels)}")

    def to_public_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "title": self.title,
            "tagline": self.tagline,
            "project": self.project_label,
            "has_blueprint": self.has_blueprint,
            "levels": [level.summary() for level in self.levels],
        }


def load_mode(folder: Path) -> Mode:
    data = json.loads((folder / MANIFEST).read_text(encoding="utf-8"))
    return Mode.model_validate({**data, "root": folder})


@cache
def all_modes() -> dict[str, Mode]:
    modes = (load_mode(folder) for folder in MODE_FOLDERS if (folder / MANIFEST).is_file())
    return {mode.key: mode for mode in modes}


def find_mode(key: str | None) -> Mode:
    modes = all_modes()
    text = (key or CLASSIC).strip().lower().replace("+", "p")
    if text in modes:
        return modes[text]
    raise KeyError(f"unknown mode {key!r}, expected one of: {', '.join(modes)}")
