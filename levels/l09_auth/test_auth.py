import time
from collections.abc import Callable

import jwt
import pytest

from levels.l09_auth.auth import (
    ADMIN_SCOPE,
    ApiKeyStore,
    AuthError,
    Forbidden,
    Principal,
    authorize,
    issue_token,
    verify_token,
)

SECRET = "test-secret-with-enough-entropy-0123456789"


def test_valid_token_gives_a_principal() -> None:
    token = issue_token(SECRET, "keeper-1", "paris", ["animals:read"])
    assert verify_token(token, SECRET) == Principal(
        "keeper-1", "paris", frozenset({"animals:read"})
    )


def test_missing_scopes_claim_means_no_scopes() -> None:
    token = jwt.encode(
        {"sub": "k", "tenant": "paris", "exp": time.time() + 60}, SECRET, algorithm="HS256"
    )
    assert verify_token(token, SECRET).scopes == frozenset()


def test_expired_token_is_rejected() -> None:
    token = issue_token(SECRET, "keeper-1", "paris", [], ttl_seconds=60, now=time.time() - 3_600)
    with pytest.raises(AuthError):
        verify_token(token, SECRET)


def test_wrong_signature_is_rejected() -> None:
    token = issue_token("another-secret-from-the-raccoon-0123456789", "raccoon", "paris", [])
    with pytest.raises(AuthError):
        verify_token(token, SECRET)


def test_alg_none_token_is_rejected() -> None:
    forged = jwt.encode(
        {"sub": "raccoon", "tenant": "paris", "exp": time.time() + 60, "scopes": [ADMIN_SCOPE]},
        None,
        algorithm="none",
    )
    with pytest.raises(AuthError):
        verify_token(forged, SECRET)


def test_token_without_tenant_is_rejected() -> None:
    token = jwt.encode({"sub": "k", "exp": time.time() + 60}, SECRET, algorithm="HS256")
    with pytest.raises(AuthError):
        verify_token(token, SECRET)


def test_token_without_expiry_is_rejected() -> None:
    token = jwt.encode({"sub": "k", "tenant": "paris"}, SECRET, algorithm="HS256")
    with pytest.raises(AuthError):
        verify_token(token, SECRET)


def test_garbage_token_is_rejected() -> None:
    with pytest.raises(AuthError):
        verify_token("not.a.jwt", SECRET)


@pytest.fixture
def store_and_key() -> tuple[ApiKeyStore, str, Principal]:
    store = ApiKeyStore()
    principal = Principal("feeder-bot", "paris", frozenset({"meals:write"}))
    return store, store.create(principal), principal


def test_api_key_authenticates(store_and_key: tuple[ApiKeyStore, str, Principal]) -> None:
    store, key, principal = store_and_key
    assert store.authenticate(key) == principal
    assert key not in repr(store._records), "only the hash of a key may be stored"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda key: key[:-1] + ("A" if key[-1] != "A" else "B"),
        lambda key: "zoo_deadbeef_" + key.split("_", 2)[2],
        lambda key: key.replace("zoo_", "pk_", 1),
        lambda key: "zoo",
        lambda key: "",
    ],
)
def test_bad_api_keys_are_rejected(
    store_and_key: tuple[ApiKeyStore, str, Principal], mutate: Callable[[str], str]
) -> None:
    store, key, _ = store_and_key
    with pytest.raises(AuthError):
        store.authenticate(mutate(key))


READER = Principal("keeper-1", "paris", frozenset({"animals:read"}))
LYON_ADMIN = Principal("raccoon", "lyon", frozenset({ADMIN_SCOPE}))


def test_scope_grants_permission() -> None:
    authorize(READER, "animals:read", "paris")


def test_missing_scope_is_forbidden() -> None:
    with pytest.raises(Forbidden):
        authorize(READER, "animals:delete", "paris")


def test_admin_has_every_permission_in_its_tenant() -> None:
    authorize(LYON_ADMIN, "animals:delete", "lyon")


def test_other_tenant_is_forbidden_even_for_admins() -> None:
    with pytest.raises(Forbidden):
        authorize(LYON_ADMIN, "animals:read", "paris")
    with pytest.raises(Forbidden):
        authorize(READER, "animals:read", "lyon")
