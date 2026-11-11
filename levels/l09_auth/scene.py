"""Scene 09: a raccoon from the Lyon shelter tries every trick to read the Paris animals."""

from __future__ import annotations

import time
from collections.abc import Callable

import jwt

from levels.l09_auth.auth import (
    ADMIN_SCOPE,
    ApiKeyStore,
    AuthError,
    Forbidden,
    Principal,
    Secret,
    authorize,
    issue_token,
    verify_token,
)
from zoo.kit import Scene

SECRET = "kennel-signing-key-do-not-share-0123456789"
ANIMALS = {"paris": ["Miso", "Hazel", "Rusty"], "lyon": ["Bandit"]}


def list_animals(token: str, tenant: str) -> list[str]:
    principal = verify_token(token, SECRET)
    authorize(principal, "animals:read", tenant)
    return ANIMALS[tenant]


def attempt(call: Callable[[], object]) -> str:
    try:
        call()
    except AuthError:
        return "401"
    except Forbidden:
        return "403"
    return "200"


def play(scene: Scene) -> None:
    keeper = issue_token(SECRET, "keeper-ana", "paris", ["animals:read"])
    status = attempt(lambda: list_animals(keeper, "paris"))
    scene.check(
        status == "200",
        "Ana, a Paris keeper, reads the Paris animals.",
        f"Ana, a legit Paris keeper, got {status}. Rex bites the keepers.",
    )

    raccoon = issue_token(SECRET, "raccoon", "lyon", [ADMIN_SCOPE])
    status = attempt(lambda: list_animals(raccoon, "paris"))
    scene.metric("cross-tenant read", status)
    scene.check(
        status == "403",
        "The raccoon is admin in Lyon, but Paris is another tenant: 403.",
        "The raccoon's Lyon token opened the Paris registry. Tenant leak.",
    )

    forged = jwt.encode(
        {"sub": "raccoon", "tenant": "paris", "exp": time.time() + 600, "scopes": [ADMIN_SCOPE]},
        None,
        algorithm="none",
    )
    status = attempt(lambda: list_animals(forged, "paris"))
    scene.metric("alg=none token", status)
    scene.check(
        status == "401",
        "An unsigned 'alg: none' token is refused.",
        "An unsigned token with 'alg: none' was accepted.",
    )

    expired = issue_token(
        SECRET, "raccoon", "paris", ["animals:read"], ttl_seconds=60, now=time.time() - 86_400
    )
    status = attempt(lambda: list_animals(expired, "paris"))
    scene.metric("expired token", status)
    scene.check(
        status == "401",
        "A token stolen yesterday has expired.",
        "A token that expired yesterday still works.",
    )

    store = ApiKeyStore()
    key = store.create(Principal("feeder-bot", "paris", frozenset({"meals:write"})))
    guess = key[:-4] + "XXXX"
    status = attempt(lambda: store.authenticate(guess))
    scene.check(status == "401", "A guessed API key is refused.", "A guessed API key was accepted.")
    scene.check(
        attempt(lambda: store.authenticate(key)) == "200",
        "The feeder bot's real API key works.",
        "The feeder bot's real API key was refused.",
    )

    leaked = f"connecting with {Secret(SECRET)}"
    scene.check(
        SECRET not in leaked,
        "Secrets print as ******** in logs.",
        "The signing key appeared in a log line.",
    )
