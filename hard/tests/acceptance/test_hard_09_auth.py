"""Ticket 09: the raccoon."""

import hashlib
import time

import jwt

from zp_testkit import SECRET, World, auth, token


def catalog(world: World, headers: dict[str, str]):  # type: ignore[no-untyped-def]
    return world.client.get("/v1/animals", params={"species": "cat"}, headers=headers)


def bearer(value: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {value}"}


def test_unsigned_tokens_are_refused(world: World) -> None:
    forged = jwt.encode(
        {"sub": "raccoon", "tenant": "paris", "exp": time.time() + 600}, None, algorithm="none"
    )
    assert catalog(world, bearer(forged)).status_code == 401


def test_tokens_signed_with_another_secret_are_refused(world: World) -> None:
    forged = token("raccoon", secret="the-raccoon-also-has-a-very-long-secret-0123456789")
    assert catalog(world, bearer(forged)).status_code == 401


def test_expired_tokens_are_refused(world: World) -> None:
    assert catalog(world, bearer(token("visitor-1", ttl_s=-60))).status_code == 401


def test_tokens_without_expiry_are_refused(world: World) -> None:
    forever = jwt.encode({"sub": "visitor-1", "tenant": "paris"}, SECRET, algorithm="HS256")
    assert catalog(world, bearer(forever)).status_code == 401


def test_a_tenant_never_sees_another_tenants_animals(world: World) -> None:
    items = catalog(world, auth("bandit", tenant="lyon")).json()["items"]
    assert items
    assert all(item["name"].startswith("lyon-") for item in items)
    paris_animal = world.sql("SELECT id FROM animals WHERE tenant = 'paris' LIMIT 1")[0]["id"]
    belly = world.client.get(
        f"/v1/animals/{paris_animal}/belly", headers=auth("bandit", tenant="lyon")
    )
    assert belly.status_code == 404


def test_a_tenant_cannot_touch_another_tenants_kittens_or_pantries(world: World) -> None:
    lyon = auth("bandit", tenant="lyon")
    assert world.client.get("/v1/kittens/pixel", headers=lyon).status_code == 404
    assert world.client.get("/v1/pantries/north", headers=lyon).status_code == 404


def store_key(world: World, key_id: str, secret: str, scopes: str = "kitchen:write") -> str:
    raw = f"zk_{key_id}_{secret}"
    world.sql(
        "INSERT INTO api_keys (key_id, key_hash, subject, tenant, scopes) "
        "VALUES (?, ?, ?, 'paris', ?)",
        (key_id, hashlib.sha256(raw.encode()).hexdigest(), "feeder-bot", scopes),
    )
    return raw


def test_bots_authenticate_with_api_keys(world: World) -> None:
    raw = store_key(world, "a1b2c3", "s3cr3t_with_underscores")
    created = world.client.post(
        "/v1/kitchen/orders", json={"animal_id": 1, "grams": 30}, headers={"X-Api-Key": raw}
    )
    assert created.status_code == 201
    wrong = world.client.post(
        "/v1/kitchen/orders",
        json={"animal_id": 1, "grams": 30},
        headers={"X-Api-Key": raw[:-1] + "X"},
    )
    assert wrong.status_code == 401


def test_kitchen_orders_need_the_kitchen_scope(world: World) -> None:
    visitor = auth("visitor-1", scopes=())
    response = world.client.post(
        "/v1/kitchen/orders", json={"animal_id": 1, "grams": 30}, headers=visitor
    )
    assert response.status_code == 403
