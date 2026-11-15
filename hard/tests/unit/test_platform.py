"""The platform works today. These tests must stay green while you build the tickets."""

from zp_testkit import World, ask, auth


def test_liveness(world: World) -> None:
    assert world.client.get("/healthz").status_code == 200


def test_the_owl_answers_with_the_zoo_facts(world: World) -> None:
    response = ask(world.client, "Why do otters hold hands?")
    assert response.status_code == 200
    assert "Sea otters hold hands" in response.json()["answer"]


def test_a_meal_fills_a_belly(world: World) -> None:
    before = world.client.get("/v1/animals/1/belly", headers=auth()).json()["grams"]
    created = world.client.post(
        "/v1/kitchen/orders", json={"animal_id": 1, "grams": 40}, headers=auth()
    )
    assert created.status_code == 201
    assert world.client.get("/v1/animals/1/belly", headers=auth()).json()["grams"] == before + 40


def test_the_catalog_lists_a_species(world: World) -> None:
    body = world.client.get("/v1/animals", params={"species": "otter"}, headers=auth()).json()
    assert body["items"]
    assert all(item["species"] == "otter" for item in body["items"])


def test_the_crew_cleans_a_reported_pen(world: World) -> None:
    world.client.post("/v1/pens/pen-lion/incidents", json={"kind": "dirty"}, headers=auth())
    world.client.post("/internal/worker/drain")
    assert world.client.get("/v1/pens/pen-lion", headers=auth()).json()["dirty"] is False
