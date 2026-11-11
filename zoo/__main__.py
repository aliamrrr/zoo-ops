"""Command line entry point: python -m zoo <test|scene|play|reset>."""

from __future__ import annotations

import argparse
import subprocess
import sys
import threading
import webbrowser

from rich.console import Console
from rich.table import Table
from rich.text import Text

from zoo.registry import LEVELS, ROOT, Level, find_level, play_level
from zoo.sprites import sprite_text
from zoo.testbench import STATUS_LABELS, bench

STARTER_TAG = "starter"
TONE_MARKS = {
    "info": ("  .  ", "grey50"),
    "good": ("  +  ", "bold #2FBF71"),
    "bad": ("  !  ", "bold #D64545"),
}


def pick_levels(keys: list[str]) -> list[Level]:
    return [find_level(key) for key in keys] if keys else list(LEVELS)


def cmd_test(args: argparse.Namespace) -> int:
    return bench(pick_levels(args.levels), verbose=args.verbose)


def cmd_scene(args: argparse.Namespace) -> int:
    console = Console(highlight=False)
    worst = 0
    for level in pick_levels(args.levels):
        result = play_level(level)
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


def cmd_play(args: argparse.Namespace) -> int:
    import uvicorn

    url = f"http://127.0.0.1:{args.port}"
    if not args.no_browser:
        threading.Timer(1.5, webbrowser.open, args=(url,)).start()
    Console().print(f"[bold]Zoo Ops[/] is open at [bold #4E9BD4]{url}[/]  (Ctrl+C to stop)")
    uvicorn.run(
        "zoo.server:app",
        host="127.0.0.1",
        port=args.port,
        reload=True,
        reload_dirs=[str(ROOT / "levels"), str(ROOT / "zoo")],
        log_level="warning",
    )
    return 0


def git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments], cwd=ROOT, capture_output=True, text=True, check=False
    )


def cmd_reset(args: argparse.Namespace) -> int:
    console = Console(highlight=False)
    top = git("rev-parse", "--show-toplevel")
    same_repo = top.returncode == 0 and top.stdout.strip().lower() == ROOT.as_posix().lower()
    if not same_repo or git("rev-parse", "--verify", "--quiet", STARTER_TAG).returncode != 0:
        console.print(
            "[bold #D64545]No starter snapshot found.[/] Create it once from the "
            'untouched project:\n  git add -A\n  git commit -m "Starter"\n'
            f"  git tag {STARTER_TAG}"
        )
        return 1
    for level in pick_levels(args.levels):
        relative = level.todo_path.relative_to(ROOT).as_posix()
        restored = git("restore", f"--source={STARTER_TAG}", "--worktree", "--", relative)
        if restored.returncode != 0:
            console.print(f"[#D64545]{relative}: {restored.stderr.strip()}[/]")
            return 1
        console.print(f"[#E3A03A]reset[/] {relative} to the starter version")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m zoo", description="Zoo Ops")
    commands = parser.add_subparsers(dest="command", required=True)

    test = commands.add_parser("test", help="run the test bench (all levels or some)")
    test.add_argument("levels", nargs="*", help="level numbers, e.g. 1 4 10")
    test.add_argument("-v", "--verbose", action="store_true", help="list every test")
    test.set_defaults(handler=cmd_test)

    scene = commands.add_parser("scene", help="play level scenes in the terminal")
    scene.add_argument("levels", nargs="*")
    scene.set_defaults(handler=cmd_scene)

    play = commands.add_parser("play", help="open the game in the browser")
    play.add_argument("--port", type=int, default=8000)
    play.add_argument("--no-browser", action="store_true")
    play.set_defaults(handler=cmd_play)

    reset = commands.add_parser("reset", help="restore a level's TODO file to the starter")
    reset.add_argument("levels", nargs="+")
    reset.set_defaults(handler=cmd_reset)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except KeyError as exc:
        Console().print(f"[#D64545]{exc.args[0]}[/]")
        return 2


if __name__ == "__main__":
    sys.exit(main())
