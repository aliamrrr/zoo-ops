"""Pixel sprites shared by the web game and the terminal (rendered with half-block characters)."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

from rich.style import Style
from rich.text import Text

SPRITES_FILE = Path(__file__).resolve().parent / "static" / "sprites.json"
TRANSPARENT = "."
UPPER_HALF = "▀"
LOWER_HALF = "▄"


@cache
def _load() -> tuple[dict[str, str], dict[str, list[str]]]:
    data = json.loads(SPRITES_FILE.read_text(encoding="utf-8"))
    return data["palette"], data["sprites"]


def palette() -> dict[str, str]:
    return _load()[0]


def sprite_text(name: str) -> Text:
    """Two pixel rows per terminal line: the top pixel is the foreground of an upper half
    block, the bottom pixel its background. A 12x12 sprite fits in 12 columns by 6 lines."""
    colors, sprites = _load()
    grid = sprites[name]
    text = Text(no_wrap=True)
    for top_row, bottom_row in zip(grid[0::2], grid[1::2], strict=True):
        for top, bottom in zip(top_row, bottom_row, strict=True):
            if top == TRANSPARENT and bottom == TRANSPARENT:
                text.append(" ")
            elif top == TRANSPARENT:
                text.append(LOWER_HALF, Style(color=colors[bottom]))
            elif bottom == TRANSPARENT:
                text.append(UPPER_HALF, Style(color=colors[top]))
            else:
                text.append(UPPER_HALF, Style(color=colors[top], bgcolor=colors[bottom]))
        text.append("\n")
    text.rstrip()
    return text


def gradient_strip(width: int) -> Text:
    """A stepped band of pixel blocks in the zoo palette, used as a header and footer."""
    colors = palette()
    bands = [colors[key] for key in ("D", "G", "y", "p", "B")]
    text = Text(no_wrap=True)
    for column in range(width):
        position = column * len(bands) // max(width, 1)
        top = bands[position]
        bottom = bands[min(position + (column % 2), len(bands) - 1)]
        text.append(UPPER_HALF, Style(color=top, bgcolor=bottom))
    return text
