"""The architecture blueprint of the hard modes: layout, checks and hints."""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import pytest

from zoo.blueprint import Blueprint, InvalidPlacement
from zoo.modes import find_mode

HARD_MODES = ["hard", "hardpp"]
BOX_W, BOX_H = 124, 44


def answers(key: str) -> dict[str, dict[str, object]]:
    data = json.loads(find_mode(key).blueprint_path.read_text(encoding="utf-8"))
    return {
        level: {"slot": answer["slots"][0], "links": answer["links"]}
        for level, answer in data["answers"].items()
    }


@pytest.mark.parametrize("key", HARD_MODES)
def test_blueprint_boxes_do_not_overlap(key: str) -> None:
    data = json.loads(find_mode(key).blueprint_path.read_text(encoding="utf-8"))
    boxes = [(item["x"], item["y"]) for item in data["components"] + data["slots"]]
    for x, y in boxes:
        assert x >= 0 and y >= 0
        assert x + BOX_W <= data["width"] and y + BOX_H <= data["height"]
    for (ax, ay), (bx, by) in itertools.combinations(boxes, 2):
        assert not (abs(ax - bx) < BOX_W and abs(ay - by) < BOX_H), (ax, ay, bx, by)


@pytest.mark.parametrize("key", HARD_MODES)
def test_every_answer_uses_real_slots_and_components(key: str) -> None:
    blueprint = Blueprint(find_mode(key))
    for level, answer in answers(key).items():
        assert level in blueprint.levels
        assert answer["slot"] in blueprint.slot_ids
        assert isinstance(answer["links"], list)
        assert set(answer["links"]) <= blueprint.component_ids


@pytest.mark.parametrize("key", HARD_MODES)
def test_the_right_design_is_accepted(key: str, tmp_path: Path) -> None:
    blueprint = Blueprint(find_mode(key), tmp_path)
    progress = blueprint.save(answers(key))
    assert progress["correct"] == 10
    assert Blueprint(find_mode(key), tmp_path).placed() == frozenset(blueprint.levels)


@pytest.mark.parametrize("key", HARD_MODES)
def test_a_wrong_design_gets_hints_but_never_the_answer(key: str, tmp_path: Path) -> None:
    blueprint = Blueprint(find_mode(key), tmp_path)
    design = answers(key)
    used = {item["slot"] for item in design.values()}
    decoy = next(slot for slot in blueprint.slot_ids if slot not in used)
    design["01"] = {"slot": decoy, "links": design["01"]["links"]}
    design["02"] = {"slot": design["02"]["slot"], "links": []}
    checks = blueprint.save(design)["checks"]
    assert checks["01"]["verdict"] == "wrong_place"
    assert checks["01"]["hint"]
    assert checks["02"]["verdict"] == "wrong_links"
    assert checks["02"]["missing"] > 0
    assert "answers" not in blueprint.public()


def test_impossible_designs_are_refused(tmp_path: Path) -> None:
    blueprint = Blueprint(find_mode("hard"), tmp_path)
    with pytest.raises(InvalidPlacement):
        blueprint.save({"01": {"slot": "nowhere", "links": []}})
    with pytest.raises(InvalidPlacement):
        blueprint.save({"01": {"slot": "s-edge"}, "02": {"slot": "s-edge"}})
    with pytest.raises(InvalidPlacement):
        blueprint.save({"01": {"slot": "s-edge", "links": ["mainframe"]}})


def test_a_corrupt_saved_design_starts_over(tmp_path: Path) -> None:
    (tmp_path / "blueprint-hard.json").write_text('{"placements": [1, 2]}', encoding="utf-8")
    progress = Blueprint(find_mode("hard"), tmp_path).progress()
    assert progress["correct"] == 0
    assert progress["placements"] == {}
