"""The three ways to play: Classic (guided TODOs), Hard (a real service), Hard++ (distributed).

Classic is described by `zoo.registry`. Each hard mode lives in its own folder with a
`zoo-mode.json` manifest, a project, its acceptance tests, tickets and an architecture blueprint.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from zoo.registry import LEVELS, ROOT

CLASSIC = "classic"
HARD_MODE_FOLDERS = {"hard": ROOT / "hard", "hardpp": ROOT / "hardpp"}


@dataclass(frozen=True)
class ModeLevel:
    id: str
    label: str
    pattern: str
    title: str
    ticket: str
    test: str
    without: str
    with_: str

    @property
    def number(self) -> int:
        return int(self.id)

    def to_public_dict(self, root: Path) -> dict[str, object]:
        return {
            "id": self.id,
            "number": self.number,
            "label": self.label,
            "pattern": self.pattern,
            "title": self.title,
            "ticket": self.ticket,
            "ticket_text": (root / self.ticket).read_text(encoding="utf-8"),
            "test": self.test,
            "without": self.without,
            "with": self.with_,
        }


@dataclass(frozen=True)
class Mode:
    key: str
    title: str
    tagline: str
    root: Path
    project: str
    tests: str
    levels: tuple[ModeLevel, ...]

    @property
    def is_classic(self) -> bool:
        return self.key == CLASSIC

    @property
    def blueprint_path(self) -> Path:
        return self.root / "architecture" / "blueprint.json"

    def find_level(self, key: str | int) -> ModeLevel:
        text = str(key).strip()
        for level in self.levels:
            if text in {level.id, str(level.number)}:
                return level
        raise KeyError(f"unknown level {key!r} in {self.title}, expected 1 to {len(self.levels)}")

    def to_public_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "title": self.title,
            "tagline": self.tagline,
            "project": f"{self.root.name}/{self.project}" if not self.is_classic else "levels",
            "has_blueprint": not self.is_classic,
            "levels": [
                {
                    "id": level.id,
                    "label": level.label,
                    "pattern": level.pattern,
                    "title": level.title,
                    "without": level.without,
                    "with": level.with_,
                }
                for level in self.levels
            ],
        }


def _classic() -> Mode:
    levels = tuple(
        ModeLevel(
            id=level.id,
            label=level.pattern,
            pattern=level.pattern,
            title=level.station,
            ticket="",
            test=f"levels/{level.slug}",
            without=level.pitch,
            with_=level.victory,
        )
        for level in LEVELS
    )
    return Mode(
        key=CLASSIC,
        title="Zoo Ops",
        tagline="Ten guided levels. Fill in the TODOs, the keepers wake up.",
        root=ROOT,
        project="levels",
        tests="levels",
        levels=levels,
    )


def _load_manifest(folder: Path) -> Mode:
    data = json.loads((folder / "zoo-mode.json").read_text(encoding="utf-8"))
    levels = tuple(
        ModeLevel(
            id=item["id"],
            label=item["label"],
            pattern=item["pattern"],
            title=item["title"],
            ticket=item["ticket"],
            test=item["test"],
            without=item["without"],
            with_=item["with"],
        )
        for item in data["levels"]
    )
    return Mode(
        key=data["key"],
        title=data["title"],
        tagline=data["tagline"],
        root=folder,
        project=data["project"],
        tests=data["tests"],
        levels=levels,
    )


@cache
def all_modes() -> dict[str, Mode]:
    modes = {CLASSIC: _classic()}
    for key, folder in HARD_MODE_FOLDERS.items():
        if (folder / "zoo-mode.json").is_file():
            modes[key] = _load_manifest(folder)
    return modes


def find_mode(key: str | None) -> Mode:
    modes = all_modes()
    text = (key or CLASSIC).strip().lower().replace("+", "p")
    if text in modes:
        return modes[text]
    raise KeyError(f"unknown mode {key!r}, expected one of: {', '.join(modes)}")
