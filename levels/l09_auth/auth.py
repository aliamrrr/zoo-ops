"""Level 09: JWT verification, API keys, per-tenant permissions and secret handling.

Authentication answers "who are you", authorization answers "may you do this here".
In a multi-tenant system "here" matters most: a valid token of shelter Lyon must never read
shelter Paris, whatever its scopes. Most leaks are a missing tenant check, not broken crypto.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass
from pathlib import Path

import jwt

ALGORITHM = "HS256"
ADMIN_SCOPE = "zoo:admin"


class AuthError(Exception):
    """Unknown caller (HTTP 401)."""


class Forbidden(Exception):
    """Known caller, not allowed (HTTP 403)."""


@dataclass(frozen=True)
class Principal:
    subject: str
    tenant: str
    scopes: frozenset[str]


def issue_token(
    secret: str,
    subject: str,
    tenant: str,
    scopes: list[str],
    ttl_seconds: int = 900,
    now: float | None = None,
) -> str:
    issued_at = int(time.time() if now is None else now)
    claims = {
        "sub": subject,
        "tenant": tenant,
        "scopes": scopes,
        "iat": issued_at,
        "exp": issued_at + ttl_seconds,
    }
    return jwt.encode(claims, secret, algorithm=ALGORITHM)


def verify_token(token: str, secret: str) -> Principal:
    """Decode and validate a JWT, return the caller as a Principal.

    Contract:
    - jwt.decode with algorithms=[ALGORITHM]: the list is pinned by the server, never read
      from the token header (that is how "alg": "none" tokens get accepted)
    - require the exp, sub and tenant claims (options={"require": [...]})
    - every PyJWT error (jwt.PyJWTError) becomes AuthError
    - scopes default to an empty set when the claim is missing
    """
    # TODO(level 09)
    raise NotImplementedError("verify_token")


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ApiKeyRecord:
    key_hash: str
    principal: Principal


class ApiKeyStore:
    """API keys look like "zoo_<key_id>_<secret>". Only the sha256 of the full key is stored:
    a database dump must not leak usable keys. key_id makes the lookup O(1)."""

    PREFIX = "zoo"

    def __init__(self) -> None:
        self._records: dict[str, ApiKeyRecord] = {}

    def create(self, principal: Principal) -> str:
        key_id = secrets.token_hex(4)
        raw_key = f"{self.PREFIX}_{key_id}_{secrets.token_urlsafe(24)}"
        self._records[key_id] = ApiKeyRecord(hash_api_key(raw_key), principal)
        return raw_key

    def authenticate(self, presented: str) -> Principal:
        """Return the principal of a valid key, raise AuthError otherwise.

        Contract:
        - split "zoo_<key_id>_<secret>" (the secret may contain "_": split at most twice),
          a wrong shape or prefix is an AuthError
        - unknown key_id is an AuthError
        - compare hash_api_key(presented) with the stored hash using hmac.compare_digest
          (constant time: a plain == leaks how many leading characters matched)
        """
        # TODO(level 09)
        raise NotImplementedError("ApiKeyStore.authenticate")


def authorize(principal: Principal, permission: str, resource_tenant: str) -> None:
    """Raise Forbidden unless `principal` may do `permission` on a resource of
    `resource_tenant`.

    Contract:
    - tenant isolation first: another tenant is always Forbidden, even with ADMIN_SCOPE
    - then scopes: `permission` itself or ADMIN_SCOPE grants it
    """
    # TODO(level 09)
    raise NotImplementedError("authorize")


class Secret:
    """Wraps a secret value so it never ends up in logs, reprs or tracebacks by accident."""

    def __init__(self, value: str) -> None:
        self._value = value

    def reveal(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "Secret('********')"

    __str__ = __repr__


def load_secret(name: str) -> Secret:
    """Read ZOO_<NAME> from the environment, or the file named by ZOO_<NAME>_FILE
    (Docker and Kubernetes mount secrets as files). No default: a missing secret must stop
    the boot instead of silently running with a placeholder."""
    env_name = f"ZOO_{name.upper()}"
    if value := os.environ.get(env_name):
        return Secret(value)
    if path := os.environ.get(f"{env_name}_FILE"):
        return Secret(Path(path).read_text(encoding="utf-8").strip())
    raise RuntimeError(f"missing secret: set {env_name} or {env_name}_FILE")
