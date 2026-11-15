from __future__ import annotations

from pathlib import Path

import pytest

from zp_testkit import World


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)


@pytest.fixture
def make_world(tmp_path: Path):  # type: ignore[no-untyped-def]
    def build(**overrides: object) -> World:
        return World(tmp_path, overrides=dict(overrides))

    return build
