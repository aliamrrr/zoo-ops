"""The `zoo` command, including `zoo reset` inside a real (temporary) git repository."""

from __future__ import annotations

import socket
import subprocess
from pathlib import Path

import pytest

from zoo import cli
from zoo.checks import StatusBoard
from zoo.runtimes import UsageError, build_runtimes

STARTER = "raise NotImplementedError('get_or_load')\n"
SOLVED = "return cached or loader()\n"


def run_git(repo: Path, *arguments: str) -> None:
    subprocess.run(["git", *arguments], cwd=repo, check=True, capture_output=True)


@pytest.fixture
def learner_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A clone of Zoo Ops with a solution committed on the learner's own branch."""
    repo = tmp_path / "zoo-ops"
    target = repo / "levels" / "l01_cache" / "cache.py"
    target.parent.mkdir(parents=True)
    target.write_text(STARTER, encoding="utf-8")
    run_git(repo, "init", "-q", "-b", "main")
    run_git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
    run_git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "starter")
    run_git(repo, "switch", "-q", "-c", "solved")
    target.write_text(SOLVED, encoding="utf-8")
    run_git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "solve 01")
    monkeypatch.setattr(cli, "ROOT", repo.resolve())
    return repo


def test_reset_restores_the_version_the_learner_started_from(learner_repo: Path) -> None:
    assert cli.main(["reset", "1"]) == 0
    target = learner_repo / "levels" / "l01_cache" / "cache.py"
    assert target.read_text(encoding="utf-8") == STARTER


def test_reset_needs_a_git_clone(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    assert cli.main(["reset", "1"]) == 1


def test_reset_explains_how_to_reset_a_hard_project() -> None:
    assert cli.main(["reset", "--mode", "hard"]) == 2
    assert cli.main(["reset"]) == 2


def test_reset_targets_follow_the_mode(tmp_path: Path) -> None:
    runtimes = build_runtimes(StatusBoard(tmp_path), tmp_path)
    assert runtimes["classic"].reset_paths(["4"], whole_project=False) == [
        "levels/l04_idempotency/idempotency.py"
    ]
    assert runtimes["hardpp"].reset_paths([], whole_project=True) == ["hardpp/src/zoo_planet"]
    with pytest.raises(UsageError):
        runtimes["hard"].scenes([])


def test_no_command_means_play() -> None:
    args = cli.build_parser().parse_args(["play", "hardpp"])
    assert (args.handler, args.mode_name) == (cli.cmd_play, "hardpp")


def test_play_picks_the_next_free_port() -> None:
    with socket.socket() as taken:
        taken.bind(("127.0.0.1", 0))
        taken.listen()
        port = taken.getsockname()[1]
        assert cli.free_port(port) != port


def test_modes_and_scenes_print(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["modes"]) == 0
    assert "zoo play hardpp" in capsys.readouterr().out
    assert cli.main(["scene", "4"]) in (0, 1)
    assert "Idempotency" in capsys.readouterr().out
