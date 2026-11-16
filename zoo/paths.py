"""Where things live. Zoo Ops runs from its repository: the game reads the levels and projects
next to the `zoo` package, and keeps its own state (test results, blueprints) in `.zoo/`, or in
`$ZOO_STATE_DIR` when set (the Docker image keeps it in a volume)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = Path(os.environ.get("ZOO_STATE_DIR") or ROOT / ".zoo")
MODE_FOLDERS = (ROOT / "levels", ROOT / "hard", ROOT / "hardpp")


def make_levels_importable() -> None:
    """Classic runs the learner's files as the `levels` package, from any working directory."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
