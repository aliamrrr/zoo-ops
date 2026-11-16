"""What the page relies on beyond the shape of the responses."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from zoo.runtimes import format_sse


def test_the_api_serves_each_mode(client: TestClient) -> None:
    assert [mode["key"] for mode in client.get("/api/modes").json()] == [
        "classic",
        "hard",
        "hardpp",
    ]
    levels = client.get("/api/levels", params={"mode": "hardpp"}).json()
    assert levels[3]["ticket_text"].startswith("# PLANET-204")
    assert client.get("/api/blueprint", params={"mode": "classic"}).status_code == 404
    assert client.get("/api/levels", params={"mode": "nightmare"}).status_code == 404
    assert client.get("/api/levels", params={"mode": "<script>"}).status_code == 422


def test_the_blueprint_never_leaks_its_answers(client: TestClient) -> None:
    body = client.get("/api/blueprint", params={"mode": "hard"}).json()
    assert "answers" not in body["blueprint"]
    refused = client.put(
        "/api/blueprint",
        params={"mode": "hard"},
        json={"placements": {"01": {"slot": "nowhere", "links": []}}},
    )
    assert refused.status_code == 422


def test_a_ticket_ships_only_with_green_tests_and_a_placed_block(client: TestClient) -> None:
    systems = client.get("/api/game/systems", params={"mode": "hard"}).json()
    assert {entry["status"] for entry in systems.values()} == {"todo"}
    assert systems["01"]["headline"] == "it works: not yet"


def test_each_app_keeps_its_own_state(make_client: Callable[[], TestClient]) -> None:
    first, second = make_client(), make_client()
    blueprint = first.get("/api/blueprint", params={"mode": "hard"}).json()
    slot = blueprint["blueprint"]["slots"][0]["id"]
    placements = {"placements": {"01": {"slot": slot}}}
    first.put("/api/blueprint", params={"mode": "hard"}, json=placements)
    saved = second.get("/api/blueprint", params={"mode": "hard"}).json()["progress"]
    assert saved["placements"] == {}


def test_static_files_are_revalidated(client: TestClient) -> None:
    assert client.get("/").headers["cache-control"] == "no-cache"
    assert client.get("/static/js/main.js").headers["cache-control"] == "no-cache"


def test_the_owl_streams_once_async_processing_is_built(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = client.app.state.runtimes["hard"]  # type: ignore[attr-defined]
    monkeypatch.setattr(runtime, "stream_formatter", lambda: format_sse)
    response = client.get(
        "/api/game/ask", params={"mode": "hard", "q": "Why do otters hold hands?"}
    )
    assert response.headers["content-type"].startswith("text/event-stream")
    for event in ("event: meta", "event: token", "event: done"):
        assert event in response.text
