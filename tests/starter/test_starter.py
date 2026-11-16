"""Guards for `main`: it must ship the exercises, never their solutions.

The level and ticket tests are red on purpose until a player solves them. These tests fail
when a solution lands on `main` by mistake, or when a TODO quietly disappears.
"""

from __future__ import annotations

import pytest

from zoo.checks import run_levels
from zoo.modes import find_mode
from zoo.registry import LEVELS, Level


@pytest.mark.parametrize("level", LEVELS, ids=lambda level: level.slug)
def test_every_classic_todo_is_still_a_todo(level: Level) -> None:
    raising = sorted(set(level.todos) - set(level.naive))
    assert sorted(level.todos_left()) == raising, (
        f"{level.relative_todo_path} no longer raises NotImplementedError for every TODO: "
        "solutions live on your own branch, never on main"
    )


@pytest.mark.slow
@pytest.mark.parametrize("key", ["hard", "hardpp"])
def test_no_hard_ticket_is_already_solved(key: str) -> None:
    mode = find_mode(key)
    reports = run_levels(mode, list(mode.levels))
    solved = sorted(level_id for level_id, report in reports.items() if report.status != "todo")
    assert not solved, f"{mode.title}: tickets {solved} are not red on main (solved or broken)"
