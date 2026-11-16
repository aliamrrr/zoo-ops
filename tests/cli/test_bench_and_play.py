"""The terminal test bench and `zoo play`, without opening a browser or a server."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from zoo import cli
from zoo.modes import Mode, find_mode
from zoo.testbench import hard_bench

PASSING = "def test_it_works():\n    assert True\n"
FAILING = "def test_it_works():\n    assert 1 == 2, 'not yet'\n"


def test_the_classic_bench_shows_every_todo(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["test", "1"]) == 1
    out = capsys.readouterr().out
    assert "CACHE" in out
    assert "needs CacheAside.get_or_load" in out
    assert cli.main(["test", "4", "10", "-v"]) == 1
    assert "IDEMPOTENCY" in capsys.readouterr().out


def test_the_whole_classic_bench_ends_with_the_scoreboard(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main(["test"]) == 1
    assert "STATIONS ONLINE" in capsys.readouterr().out


def test_the_hard_bench_needs_green_tests_and_a_placed_block(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    tiny_mode: Callable[[Path, list[str]], Mode],
) -> None:
    mode = tiny_mode(tmp_path, [PASSING, FAILING])
    assert hard_bench(mode, list(mode.levels), frozenset({"01"}), verbose=False) == 1
    out = capsys.readouterr().out
    assert "ONLINE" in out and "not yet" in out
    assert hard_bench(mode, list(mode.levels[:1]), frozenset(), verbose=True) == 0
    assert "place block 01 first" in capsys.readouterr().out


def test_play_asks_for_a_mode_and_serves_it(monkeypatch: pytest.MonkeyPatch) -> None:
    served: dict[str, Any] = {}
    monkeypatch.setattr("uvicorn.run", lambda app, **options: served.update(options, app=app))
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda *args, **kwargs: "3")
    monkeypatch.delenv("ZOO_MODE", raising=False)
    monkeypatch.delenv("ZOO_PUBLIC_PORT", raising=False)
    opened: list[str] = []
    monkeypatch.setattr(cli, "open_browser", opened.append)
    monkeypatch.setattr("threading.Timer", lambda delay, call, args: _Now(call, args))

    assert cli.main(["play", "--port", "8765"]) == 0
    assert served["app"] == "zoo.server:app"
    assert served["host"] == "127.0.0.1" and served["reload"] is True
    assert opened and opened[0].endswith("/?mode=hardpp")


def test_play_takes_the_mode_from_the_command_or_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    urls: list[str] = []
    monkeypatch.setattr("uvicorn.run", lambda app, **options: None)
    monkeypatch.setattr(cli, "open_browser", urls.append)
    monkeypatch.setattr("threading.Timer", lambda delay, call, args: _Now(call, args))
    cli.main(["play", "hard", "--no-reload"])
    monkeypatch.setenv("ZOO_MODE", "hardpp")
    cli.main(["play"])
    monkeypatch.setenv("ZOO_NO_BROWSER", "1")
    cli.main(["play", "classic"])
    assert [url.rsplit("=", 1)[1] for url in urls] == ["hard", "hardpp"]
    assert find_mode("hard++").key == "hardpp"


class _Now:
    """threading.Timer stand-in that runs at once."""

    def __init__(self, call: Any, args: tuple[Any, ...]) -> None:
        self._call, self._args = call, args

    def start(self) -> None:
        self._call(*self._args)
