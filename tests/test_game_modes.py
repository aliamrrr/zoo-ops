"""The game shell around the three modes: manifests, blueprints, the API and the live hooks."""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from zoo.blueprint import Blueprint, InvalidPlacement
from zoo.game import MEAL_GRAMS, SimulatedBackend
from zoo.modes import all_modes, find_mode
from zoo.server import app

HARD_MODES = ["hard", "hardpp"]
BOX_W, BOX_H = 124, 44


def answers(key: str) -> dict[str, dict[str, object]]:
    data = json.loads(find_mode(key).blueprint_path.read_text(encoding="utf-8"))
    return {
        level: {"slot": answer["slots"][0], "links": answer["links"]}
        for level, answer in data["answers"].items()
    }


def test_three_modes_are_available() -> None:
    assert list(all_modes()) == ["classic", *HARD_MODES]
    assert find_mode("Hard++").key == "hardpp"
    with pytest.raises(KeyError):
        find_mode("nightmare")


@pytest.mark.parametrize("key", HARD_MODES)
def test_every_ticket_has_its_file_and_its_tests(key: str) -> None:
    mode = find_mode(key)
    assert [level.id for level in mode.levels] == [f"{n:02d}" for n in range(1, 11)]
    for level in mode.levels:
        assert (mode.root / level.ticket).is_file()
        assert (mode.root / level.test).is_file()
    assert (mode.root / mode.project).is_dir()


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
def test_the_right_design_is_accepted(key: str, tmp_path: Path) -> None:
    blueprint = Blueprint(find_mode(key), tmp_path)
    progress = blueprint.save(answers(key))
    assert progress["correct"] == 10
    assert Blueprint(find_mode(key), tmp_path).progress()["correct"] == 10


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


def test_the_api_serves_each_mode() -> None:
    client = TestClient(app)
    assert [mode["key"] for mode in client.get("/api/modes").json()] == ["classic", *HARD_MODES]
    levels = client.get("/api/levels", params={"mode": "hardpp"}).json()
    assert levels[3]["ticket_text"].startswith("# PLANET-204")
    assert client.get("/api/blueprint", params={"mode": "classic"}).status_code == 404
    assert client.get("/api/levels", params={"mode": "nightmare"}).status_code == 404
    body = client.get("/api/blueprint", params={"mode": "hard"}).json()
    assert "answers" not in body["blueprint"]
    refused = client.put(
        "/api/blueprint",
        params={"mode": "hard"},
        json={"placements": {"01": {"slot": "nowhere", "links": []}}},
    )
    assert refused.status_code == 422


def test_the_simulated_kiosk_follows_the_shipped_tickets() -> None:
    backend = SimulatedBackend()
    question = "Why do otters hold hands?"
    assert backend.ask(question, storm=False).provider == "owl"
    assert backend.ask(question, storm=False).provider == "owl"
    assert backend.ask(question, storm=True).failed

    backend.online = frozenset({"01", "03"})
    backend.reset()
    backend.ask(question, storm=False)
    assert backend.ask(question, storm=False).cache_hit
    assert backend.ask("How strong is an ant?", storm=True).provider == "parrot"


def test_simulated_meals_are_served_once_with_idempotency() -> None:
    backend = SimulatedBackend()
    backend.online = frozenset({"04"})
    for _ in range(20):
        assert backend.feed("lion").delivered_grams == MEAL_GRAMS
    backend.online = frozenset()
    meals = {backend.feed("lion").delivered_grams for _ in range(40)}
    assert max(meals) > MEAL_GRAMS
