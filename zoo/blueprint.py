"""The architecture blueprint of a hard mode: where each pattern belongs and what it talks to.

The page only ever receives the public part of the blueprint. Answers stay on the server and a
placement is checked here, so the right slot cannot be read from the browser's network tab.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from zoo.modes import Mode
from zoo.registry import ROOT

Verdict = Literal["correct", "wrong_place", "wrong_links", "unplaced"]
PUBLIC_KEYS = ("title", "intro", "width", "height", "components", "edges", "slots", "blocks")
STATE_DIR = ROOT / ".zoo"


@dataclass(frozen=True)
class Placement:
    slot: str | None
    links: frozenset[str]


@dataclass(frozen=True)
class BlockCheck:
    verdict: Verdict
    missing: int
    extra: int
    hint: str

    def to_dict(self) -> dict[str, object]:
        return {
            "verdict": self.verdict,
            "missing": self.missing,
            "extra": self.extra,
            "hint": self.hint,
        }


class InvalidPlacement(ValueError):
    """The page sent a slot, component or level the blueprint does not have."""


class Blueprint:
    def __init__(self, mode: Mode, state_dir: Path = STATE_DIR) -> None:
        self.mode = mode
        self._data = json.loads(mode.blueprint_path.read_text(encoding="utf-8"))
        self._state_path = state_dir / f"blueprint-{mode.key}.json"
        self.slot_ids = frozenset(slot["id"] for slot in self._data["slots"])
        self.component_ids = frozenset(item["id"] for item in self._data["components"])
        self.levels = tuple(block["level"] for block in self._data["blocks"])

    def public(self) -> dict[str, object]:
        return {key: self._data[key] for key in PUBLIC_KEYS}

    def parse(self, raw: dict[str, dict[str, object]]) -> dict[str, Placement]:
        placements: dict[str, Placement] = {}
        used_slots: set[str] = set()
        for level, item in raw.items():
            if level not in self.levels:
                raise InvalidPlacement(f"unknown block {level!r}")
            slot = item.get("slot")
            links = frozenset(item.get("links") or ())
            if slot is not None and slot not in self.slot_ids:
                raise InvalidPlacement(f"unknown slot {slot!r}")
            if slot is not None and slot in used_slots:
                raise InvalidPlacement(f"two blocks sit on {slot!r}")
            unknown = links - self.component_ids
            if unknown:
                raise InvalidPlacement(f"unknown components {sorted(unknown)}")
            if slot is not None:
                used_slots.add(slot)
            placements[level] = Placement(slot, links)
        return placements

    def check_block(self, level: str, placement: Placement | None) -> BlockCheck:
        answer = self._data["answers"][level]
        if placement is None or placement.slot is None:
            return BlockCheck("unplaced", len(answer["links"]), 0, "")
        expected = frozenset(answer["links"])
        missing = len(expected - placement.links)
        extra = len(placement.links - expected)
        if placement.slot not in answer["slots"]:
            return BlockCheck("wrong_place", missing, extra, answer["hint"])
        if missing or extra:
            return BlockCheck("wrong_links", missing, extra, answer["hint"])
        return BlockCheck("correct", 0, 0, "")

    def check(self, placements: dict[str, Placement]) -> dict[str, BlockCheck]:
        return {level: self.check_block(level, placements.get(level)) for level in self.levels}

    def save(self, raw: dict[str, dict[str, object]]) -> dict[str, object]:
        placements = self.parse(raw)
        checks = self.check(placements)
        stored = {
            level: {"slot": placement.slot, "links": sorted(placement.links)}
            for level, placement in placements.items()
        }
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(json.dumps({"placements": stored}), encoding="utf-8")
        return self._progress(stored, checks)

    def progress(self) -> dict[str, object]:
        try:
            stored = json.loads(self._state_path.read_text(encoding="utf-8"))["placements"]
            placements = self.parse(stored)
        except (OSError, ValueError, KeyError, InvalidPlacement):
            stored, placements = {}, {}
        return self._progress(stored, self.check(placements))

    def _progress(
        self, stored: dict[str, object], checks: dict[str, BlockCheck]
    ) -> dict[str, object]:
        return {
            "placements": stored,
            "checks": {level: check.to_dict() for level, check in checks.items()},
            "correct": sum(check.verdict == "correct" for check in checks.values()),
            "total": len(checks),
        }

    def is_placed(self, level: str) -> bool:
        return self.progress()["checks"][level]["verdict"] == "correct"  # type: ignore[index]
