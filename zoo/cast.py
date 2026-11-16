"""The ten keepers. Every mode teaches the same ten patterns, so pattern 04 always wakes Miso."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Keeper:
    name: str
    animal: str


KEEPERS: dict[str, Keeper] = {
    "01": Keeper("Hazel the squirrel", "squirrel"),
    "02": Keeper("Gus the goose", "goose"),
    "03": Keeper("Rusty the fox", "fox"),
    "04": Keeper("Miso the cat", "cat"),
    "05": Keeper("Mika the meerkat", "meerkat"),
    "06": Keeper("Digby the mole", "mole"),
    "07": Keeper("Bea the beaver", "beaver"),
    "08": Keeper("The ant colony", "ant"),
    "09": Keeper("Rex the guard dog", "dog"),
    "10": Keeper("Pip the canary", "canary"),
}
