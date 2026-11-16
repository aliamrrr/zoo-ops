"""The JSON contract between the server and the page.

The page reads these responses field by field, so their shape (keys and value types, not the
values) is pinned in `contract.json`. A refactor of the server must leave it unchanged.
Regenerate it on purpose only: ZOO_UPDATE_CONTRACT=1 pytest tests/api/test_contract.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

CONTRACT = Path(__file__).with_name("contract.json")
# Free-form maps whose keys depend on the level, the scene or the test names.
OPAQUE_KEYS = {"metrics", "placements"}


def shape(value: Any, key: str = "") -> Any:
    if key in OPAQUE_KEYS:
        return "map"
    if isinstance(value, dict):
        return {name: shape(item, name) for name, item in sorted(value.items())}
    if isinstance(value, list):
        return [shape(value[0])] if value else []
    return type(value).__name__


def responses(client: TestClient) -> dict[str, Any]:
    calls: dict[str, Any] = {
        "GET /api/modes": client.get("/api/modes"),
        "GET /api/game/questions": client.get("/api/game/questions"),
        "POST /api/levels/01/play": client.post("/api/levels/01/play"),
        "GET /healthz": client.get("/healthz"),
        "GET /readyz": client.get("/readyz"),
    }
    for mode in ("classic", "hard", "hardpp"):
        params = {"mode": mode}
        calls[f"GET /api/levels {mode}"] = client.get("/api/levels", params=params)
        calls[f"GET /api/game/systems {mode}"] = client.get("/api/game/systems", params=params)
        calls[f"POST /api/game/reset {mode}"] = client.post("/api/game/reset", params=params)
        calls[f"POST /api/game/feed {mode}"] = client.post(
            "/api/game/feed", params={**params, "animal": "lion"}
        )
        calls[f"GET /api/game/ask {mode}"] = client.get(
            "/api/game/ask", params={**params, "q": "Why do otters hold hands?"}
        )
    for mode in ("hard", "hardpp"):
        calls[f"GET /api/blueprint {mode}"] = client.get("/api/blueprint", params={"mode": mode})
        calls[f"PUT /api/blueprint {mode}"] = client.put(
            "/api/blueprint", params={"mode": mode}, json={"placements": {}}
        )
    calls["GET /api/blueprint classic"] = client.get("/api/blueprint", params={"mode": "classic"})
    calls["GET /api/levels unknown"] = client.get("/api/levels", params={"mode": "nightmare"})

    result = {}
    for name, response in calls.items():
        body = response.json() if "json" in response.headers.get("content-type", "") else None
        result[name] = {"status": response.status_code, "body": shape(body)}
    return result


def test_every_response_keeps_its_shape(client: TestClient) -> None:
    actual = responses(client)
    if os.environ.get("ZOO_UPDATE_CONTRACT") or not CONTRACT.is_file():
        CONTRACT.write_text(json.dumps(actual, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    expected = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert actual == expected
