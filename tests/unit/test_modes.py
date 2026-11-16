"""The three manifests: every level points at real files, and broken manifests are refused."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from zoo.modes import Mode, all_modes, find_mode, load_mode
from zoo.registry import LEVELS, find_level

HARD_MODES = ["hard", "hardpp"]


def test_three_modes_are_available() -> None:
    assert list(all_modes()) == ["classic", *HARD_MODES]
    assert find_mode(None).key == "classic"
    assert find_mode("Hard++").key == "hardpp"
    with pytest.raises(KeyError):
        find_mode("nightmare")


@pytest.mark.parametrize("key", ["classic", *HARD_MODES])
def test_every_mode_has_ten_levels(key: str) -> None:
    mode = find_mode(key)
    assert [level.id for level in mode.levels] == [f"{n:02d}" for n in range(1, 11)]
    assert mode.project_path.is_dir()


def test_every_classic_level_has_its_files() -> None:
    assert len(LEVELS) == 10
    for level in LEVELS:
        assert level.todo_path.is_file(), level.todo_path
        assert (level.folder / "scene.py").is_file()
        assert (level.folder / "README.md").is_file()
        assert list(level.folder.glob("test_*.py")), level.slug
    assert find_level("l03_reliability") is find_level(3) is find_level("03")


@pytest.mark.parametrize("key", HARD_MODES)
def test_every_ticket_has_its_file_and_its_tests(key: str) -> None:
    mode = find_mode(key)
    assert mode.has_blueprint
    for level in mode.levels:
        assert (mode.root / str(level.ticket)).is_file()
        assert (mode.root / level.test).is_file()


def test_classic_has_no_blueprint() -> None:
    assert not find_mode("classic").has_blueprint
    assert find_mode("classic").project_label == "levels"
    assert find_mode("hard").project_label == "hard/src/zoo_platform"


def write_manifest(folder: Path, text: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "zoo-mode.json").write_text(text, encoding="utf-8")
    return folder


LEVEL = (
    '{"id": "01", "label": "Cache", "pattern": "Cache", "title": "T", "test": "t.py", '
    '"without": "slow", "with": "fast"%s}'
)
MANIFEST = (
    '{"key": "mini", "title": "Mini", "tagline": "t", "runtime": "%s", "project": ".", '
    '"tests": ".", "levels": [%s]}'
)


def test_a_valid_manifest_loads(tmp_path: Path) -> None:
    folder = write_manifest(tmp_path, MANIFEST % ("acceptance", LEVEL % ', "ticket": "t.md"'))
    mode = load_mode(folder)
    assert isinstance(mode, Mode)
    assert mode.find_level(1).with_ == "fast"


@pytest.mark.parametrize(
    ("runtime", "level"),
    [
        ("acceptance", LEVEL % ""),  # a hard level without its ticket
        ("classic", LEVEL % ""),  # a Classic level without its exercise
        ("acceptance", LEVEL.replace('"01"', '"02"') % ', "ticket": "t.md"'),  # ids skip 01
        ("acceptance", LEVEL % ', "ticket": "t.md", "typo": 1'),  # unknown field
    ],
)
def test_a_broken_manifest_is_refused_at_load(tmp_path: Path, runtime: str, level: str) -> None:
    with pytest.raises(ValidationError):
        load_mode(write_manifest(tmp_path, MANIFEST % (runtime, level)))
