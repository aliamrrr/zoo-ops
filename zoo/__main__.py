"""Command line entry point: python -m zoo <modes|test|scene|play|reset> [--mode MODE]."""

from __future__ import annotations

import argparse
import subprocess
import sys
import threading
import webbrowser

from rich.console import Console
from rich.table import Table
from rich.text import Text

from zoo.modes import Mode, all_modes, find_mode
from zoo.registry import LEVELS, ROOT, Level, find_level, play_level
from zoo.sprites import sprite_text
from zoo.testbench import STATUS_LABELS, bench, hard_bench

STARTER_TAG = "starter"
TONE_MARKS = {
    "info": ("  .  ", "grey50"),
    "good": ("  +  ", "bold #2FBF71"),
    "bad": ("  !  ", "bold #D64545"),
}


def pick_levels(keys: list[str]) -> list[Level]:
    return [find_level(key) for key in keys] if keys else list(LEVELS)


def cmd_modes(args: argparse.Namespace) -> int:
    console = Console(highlight=False)
    for mode in all_modes().values():
        console.print(Text.assemble((f"{mode.key:<8}", "bold"), (mode.title, "bold #4E9BD4")))
        console.print(Text(f"        {mode.tagline}", style="grey62"))
        console.print(Text(f"        python -m zoo play --mode {mode.key}\n", style="grey50"))
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    mode = find_mode(args.mode)
    if mode.is_classic:
        return bench(pick_levels(args.levels), verbose=args.verbose)
    levels = [mode.find_level(key) for key in args.levels] if args.levels else list(mode.levels)
    return hard_bench(mode, levels, verbose=args.verbose)


def classic_only(mode: Mode, command: str) -> None:
    if not mode.is_classic:
        raise KeyError(
            f"{command} is a Classic mode command, {mode.title} has acceptance "
            f"tests instead: python -m zoo test --mode {mode.key}"
        )


def cmd_scene(args: argparse.Namespace) -> int:
    classic_only(find_mode(args.mode), "scene")
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

    mode = find_mode(args.mode)
    url = f"http://127.0.0.1:{args.port}/?mode={mode.key}"
    if not args.no_browser:
        threading.Timer(1.5, webbrowser.open, args=(url,)).start()
    Console().print(
        Text.assemble(
            (mode.title, "bold"), " is open at ", (url, "bold #4E9BD4"), "  (Ctrl+C to stop)"
        )
    )
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


def starter_tag(mode: Mode) -> str:
    """Classic levels reset from `starter`, each hard project from its own `<mode>-starter`."""
    return STARTER_TAG if mode.is_classic else f"{mode.key}-{STARTER_TAG}"


def restore(console: Console, tag: str, relative: str) -> bool:
    restored = git("restore", f"--source={tag}", "--worktree", "--", relative)
    if restored.returncode != 0:
        console.print(f"[#D64545]{relative}: {restored.stderr.strip()}[/]")
        return False
    console.print(f"[#E3A03A]reset[/] {relative} to the starter version")
    return True


def cmd_reset(args: argparse.Namespace) -> int:
    console = Console(highlight=False)
    mode = find_mode(args.mode)
    if not mode.is_classic and not args.project:
        console.print(
            Text(
                f"A {mode.title} ticket touches many files, so the whole project is reset at "
                f"once.\nThis discards every change in {mode.root.name}/{mode.project}:\n"
                f"  python -m zoo reset --mode {mode.key} --project"
            )
        )
        return 1
    if mode.is_classic and not args.levels:
        raise KeyError("name the levels to reset, e.g. python -m zoo reset 3")
    top = git("rev-parse", "--show-toplevel")
    same_repo = top.returncode == 0 and top.stdout.strip().lower() == ROOT.as_posix().lower()
    tag = starter_tag(mode)
    if not same_repo or git("rev-parse", "--verify", "--quiet", tag).returncode != 0:
        console.print(
            "[bold #D64545]No starter snapshot found.[/] Fetch it with git fetch --tags, "
            "or create it once from the untouched project:\n"
            '  git add -A\n  git commit -m "Starter"\n'
            f"  git tag {tag}"
        )
        return 1
    if not mode.is_classic:
        project = (mode.root / mode.project).relative_to(ROOT).as_posix()
        return 0 if restore(console, tag, project) else 1
    for level in pick_levels(args.levels):
        if not restore(console, tag, level.todo_path.relative_to(ROOT).as_posix()):
            return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m zoo", description="Zoo Ops")
    commands = parser.add_subparsers(dest="command", required=True)
    mode_help = "classic (default), hard or hardpp"

    modes = commands.add_parser("modes", help="list the ways to play")
    modes.set_defaults(handler=cmd_modes)

    test = commands.add_parser("test", help="run the test bench (all levels or some)")
    test.add_argument("--mode", default="classic", help=mode_help)
    test.add_argument("levels", nargs="*", help="level numbers, e.g. 1 4 10")
    test.add_argument("-v", "--verbose", action="store_true", help="list every test")
    test.set_defaults(handler=cmd_test)

    scene = commands.add_parser("scene", help="play level scenes in the terminal")
    scene.add_argument("levels", nargs="*")
    scene.add_argument("--mode", default="classic", help=mode_help)
    scene.set_defaults(handler=cmd_scene)

    play = commands.add_parser("play", help="open the game in the browser")
    play.add_argument("--port", type=int, default=8000)
    play.add_argument("--no-browser", action="store_true")
    play.add_argument("--mode", default="classic", help=mode_help)
    play.set_defaults(handler=cmd_play)

    reset = commands.add_parser("reset", help="restore learner files to the starter version")
    reset.add_argument("levels", nargs="*", help="Classic: the levels to reset")
    reset.add_argument("--mode", default="classic", help=mode_help)
    reset.add_argument("--project", action="store_true", help="hard modes: reset the project")
    reset.set_defaults(handler=cmd_reset)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except KeyError as exc:
        Console().print(Text(str(exc.args[0]), style="#D64545"))
        return 2


if __name__ == "__main__":
    sys.exit(main())
