"""Runtime configuration, read from ZOO_* environment variables."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, fields


@dataclass(frozen=True, slots=True)
class Settings:
    environment: str = "dev"
    jwt_secret: str = "dev-only-secret-change-me-in-production-0123456789"
    database_path: str = "zoo_platform.db"
    redis_url: str = ""
    owl_model: str = "owl-large"
    parrot_model: str = "parrot-small"
    canary_owl_model: str = "owl-large-v2"
    canary_percent: float = 0.0
    log_level: str = "INFO"

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> Settings:
        values: dict[str, object] = {}
        for field in fields(cls):
            raw = env.get(f"ZOO_{field.name.upper()}")
            if raw is not None:
                values[field.name] = type(field.default)(raw)
        return cls(**values)
