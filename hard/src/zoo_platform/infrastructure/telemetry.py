"""Logging setup for the `zoo` logger tree."""

from __future__ import annotations

import logging
from typing import TextIO


def configure_logging(stream: TextIO, level: str) -> None:
    root = logging.getLogger("zoo")
    for handler in list(root.handlers):
        root.removeHandler(handler)
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root.addHandler(handler)
    root.setLevel(level)
    root.propagate = False
