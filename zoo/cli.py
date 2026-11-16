"""The `zoo` command (also `python -m zoo`).

zoo                      choose a mode, then play
zoo play hard            play a mode directly: classic, hard or hardpp
zoo test 3               run the tests of level 3 (zoo test --mode hard 3 for a ticket)
zoo scene 4              play the story of Classic level 4 in the terminal
zoo reset 4              restore level 4 to the version you started from
zoo modes                list the modes
"""

from __future__ import annotations

import argparse
import os
import platform
import socket
import subprocess
import sys
import threading
import webbrowser
from collections.abc import Sequence

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from zoo.checks import StatusBoard
from zoo.modes import CLASSIC, Mode, all_modes, find_mode
from zoo.paths import ROOT
from zoo.runtimes import ModeRuntime, UsageError, build_runtimes
from zoo.sprites import sprite_text
from zoo.testbench import STATUS_LABELS

TONE_MARKS = {
    "info": ("  .  ", "grey50"),
    "good": ("  +  ", "bold #2FBF71"),
    "bad": ("  !  ", "bold #D64545"),
}
BLUE = "#4E9BD4"
RED = "#D64545"


def runtime_for(mode_key: str | None) -> ModeRuntime:
    return build_runtimes(StatusBoard())[find_mode(mode_key).key]


def cmd_modes(args: argparse.Namespace) -> int:
    console = Console(highlight=False)
    for mode in all_modes().values():
        console.print(Text.assemble((f"{mode.key:<8}", "bold"), (mode.title, f"bold {BLUE}")))
        console.print(Text(f"        {mode.tagline}", style="grey62"))
        console.print(Text(f"        zoo play {mode.key}\n", style="grey50"))
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    return runtime_for(args.mode).bench(args.levels, verbose=args.verbose)


def cmd_scene(args: argparse.Namespace) -> int:
    console = Console(highlight=False)
    worst = 0
    for level, result in runtime_for(args.mode).scenes(args.levels):
        label, style = STATUS_LABELS[result.status]
        header = Table.grid(padding=(0, 3))
        header.add_row(
            sprite_text(level.animal),
            Text.assemble(
                (f"{level.id} {level.station}\n", "bold"),
                (f"{level.pattern}\n\n", "grey50"),
                (label, style),
                ("  ", ""),
                (result.headline, ""),
            ),
        )
        console.print(header)
        for event in result.events:
            mark, mark_style = TONE_MARKS[event.tone]
            console.print(Text.assemble((mark, mark_style), event.text))
        for name, value in result.metrics.items():
            console.print(Text.assemble(("     ", ""), (f"{name}: ", "grey50"), (value, "bold")))
        console.print()
        worst = max(worst, 0 if result.status == "healthy" else 1)
    return worst


def choose_mode(console: Console) -> Mode:
    """Ask which zoo to run, when a person is at the keyboard and named no mode."""
    modes = list(all_modes().values())
    console.print(Text("\nWhich zoo do you want to run?\n", style="bold"))
    for number, mode in enumerate(modes, start=1):
        console.print(
            Text.assemble(
                (f"  {number}  ", f"bold {BLUE}"), (f"{mode.title:<18}", "bold"), mode.tagline
            )
        )
    console.print()
    choices = [str(number) for number in range(1, len(modes) + 1)]
    picked = Prompt.ask("Your choice", choices=choices, default="1", console=console)
    return modes[int(picked) - 1]


def open_browser(url: str) -> None:
    """Open the game tab. Under WSL the browser lives on the Windows side."""
    if "microsoft" in platform.release().lower():
        subprocess.run(["explorer.exe", url], check=False, capture_output=True)
    else:
        webbrowser.open(url)


def interactive() -> bool:
    """A person at a terminal, who can answer a question (not CI, not a pipe)."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes"}


def free_port(preferred: int) -> int:
    """The preferred port, or the next free one: a second game, or another app, may hold it."""
    for port in range(preferred, preferred + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            if probe.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise UsageError(f"no free port between {preferred} and {preferred + 49}")


def cmd_play(args: argparse.Namespace) -> int:
    import uvicorn

    console = Console(highlight=False)
    key = args.mode_name or args.mode or os.environ.get("ZOO_MODE") or None
    mode = choose_mode(console) if key is None and interactive() else find_mode(key or CLASSIC)
    port = free_port(args.port)
    # In a container the browser reaches the port Docker publishes, not the one inside.
    shown_port = os.environ.get("ZOO_PUBLIC_PORT") or port
    url = f"http://localhost:{shown_port}/?mode={mode.key}"
    if not (args.no_browser or env_flag("ZOO_NO_BROWSER")):
        threading.Timer(1.5, open_browser, args=(url,)).start()
    reload = not args.no_reload
    hint = "Edit your code and save: the game reloads by itself. " if reload else ""
    console.print(
        Text.assemble(
            "\n",
            (mode.title, "bold"),
            " is open at ",
            (url, f"bold {BLUE}"),
            "\n",
            (f"{hint}Ctrl+C to stop.\n", "grey62"),
        )
    )
    uvicorn.run(
        "zoo.server:app",
        host=args.host,
        port=port,
        reload=reload,
        reload_dirs=[str(ROOT / "levels"), str(ROOT / "zoo")] if reload else None,
        log_level="warning",
        timeout_graceful_shutdown=20,
    )
    return 0


def git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments], cwd=ROOT, capture_output=True, text=True, check=False
    )


def starter_commit() -> str | None:
    """The commit the learner started from: where their branch left the published main.

    No tags to fetch or to keep up to date: a fresh clone, a branch with solutions on it and a
    main with local commits all reset to the starter files they began with.
    """
    top = git("rev-parse", "--show-toplevel")
    if top.returncode != 0 or top.stdout.strip().lower() != ROOT.as_posix().lower():
        return None
    for upstream in ("origin/main", "main", "starter"):
        if git("rev-parse", "--verify", "--quiet", upstream).returncode == 0:
            base = git("merge-base", "HEAD", upstream)
            if base.returncode == 0:
                return base.stdout.strip()
    return None


def cmd_reset(args: argparse.Namespace) -> int:
    console = Console(highlight=False)
    paths = runtime_for(args.mode).reset_paths(args.levels, whole_project=args.project)
    commit = starter_commit()
    if commit is None:
        console.print(
            f"[bold {RED}]No starter version found.[/] Reset works in a git clone of Zoo Ops:\n"
            "  git clone https://github.com/aliamrrr/zoo-ops.git"
        )
        return 1
    for relative in paths:
        restored = git("restore", f"--source={commit}", "--worktree", "--", relative)
        if restored.returncode != 0:
            console.print(f"[{RED}]{relative}: {restored.stderr.strip()}[/]")
            return 1
        console.print(f"[#E3A03A]reset[/] {relative} to the version you started from")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zoo",
        description="Zoo Ops: learn backend system design by keeping a zoo alive.",
        epilog="With no command, zoo asks which mode to play and opens the game.",
    )
    commands = parser.add_subparsers(dest="command")
    mode_help = "classic (default), hard or hardpp"

    modes = commands.add_parser("modes", help="list the ways to play")
    modes.set_defaults(handler=cmd_modes)

    play = commands.add_parser("play", help="open the game in the browser")
    play.add_argument("mode_name", nargs="?", metavar="MODE", help=mode_help)
    play.add_argument("--mode", default=None, help=argparse.SUPPRESS)
    play.add_argument("--port", type=int, default=8000, help="first port to try (8000)")
    host = os.environ.get("ZOO_HOST", "127.0.0.1")
    play.add_argument("--host", default=host, help=argparse.SUPPRESS)
    play.add_argument("--no-browser", action="store_true", help="do not open a browser tab")
    play.add_argument("--no-reload", action="store_true", help=argparse.SUPPRESS)
    play.set_defaults(handler=cmd_play)

    test = commands.add_parser("test", help="run the test bench (all levels or some)")
    test.add_argument("levels", nargs="*", help="level numbers, e.g. 1 4 10")
    test.add_argument("--mode", default=CLASSIC, help=mode_help)
    test.add_argument("-v", "--verbose", action="store_true", help="list every test")
    test.set_defaults(handler=cmd_test)

    scene = commands.add_parser("scene", help="play Classic level stories in the terminal")
    scene.add_argument("levels", nargs="*")
    scene.add_argument("--mode", default=CLASSIC, help=argparse.SUPPRESS)
    scene.set_defaults(handler=cmd_scene)

    reset = commands.add_parser("reset", help="restore your files to the version you started from")
    reset.add_argument("levels", nargs="*", help="Classic: the levels to reset")
    reset.add_argument("--mode", default=CLASSIC, help=mode_help)
    reset.add_argument("--project", action="store_true", help="reset every file of the mode")
    reset.set_defaults(handler=cmd_reset)
    return parser


def use_utf8_console() -> None:
    """The keepers and progress bars are Unicode art, and older Windows consoles still start
    on a legacy code page (cp1252) that cannot print them."""
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main(argv: Sequence[str] | None = None) -> int:
    use_utf8_console()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        args = parser.parse_args(["play"])
    try:
        code: int = args.handler(args)
    except (KeyError, UsageError) as exc:
        Console(soft_wrap=True).print(Text(str(exc.args[0]), style=RED))
        return 2
    return code
