"""Who is calling: turns request credentials into a Principal."""

from __future__ import annotations

from collections.abc import Mapping

import jwt

from zoo_platform.domain.errors import Unauthorized
from zoo_platform.domain.models import Principal
from zoo_platform.settings import Settings


def authenticate(headers: Mapping[str, str], settings: Settings) -> Principal:
    authorization = headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        raise Unauthorized("missing bearer token")
    try:
        claims = jwt.decode(authorization[7:], options={"verify_signature": False})
    except jwt.PyJWTError as exc:
        raise Unauthorized("malformed token") from exc
    return Principal(
        subject=str(claims.get("sub", "anonymous")),
        tenant=str(claims.get("tenant", "public")),
        scopes=frozenset(claims.get("scopes", [])),
    )
