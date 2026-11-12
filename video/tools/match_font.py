"""Find the open-license font closest to lettering seen in a frame.

    python match_font.py <fonts_dir> <frame.png> "<text>" x0 y0 x1 y1 [serif|sans]

Crops the dark lettering inside the box, renders the same text in every candidate font across
weights (and optical sizes), and ranks them by overlap (IoU) once scaled to the same height.
`width` is candidate width / reference width at equal height: 1.00 means identical spacing.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

fonts_dir, frame, text = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
box = tuple(map(int, sys.argv[4:8]))
SANS = {"inter", "dmsans", "hankengrotesk", "figtree", "albertsans", "instrumentsans", "onest", "geist", "manrope",
        "schibstedgrotesk", "bricolagegrotesque", "worksans"}
kind = sys.argv[8] if len(sys.argv) > 8 else "serif"

def tight(ink):
    ys, xs = np.where(ink > 0.5)
    return ink[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

ref = np.asarray(Image.open(frame).convert("L").crop(box), float)
ref = tight(np.clip((150 - ref) / 110, 0, 1))
H, W = ref.shape
print(f"reference lettering: {W} x {H} px")

def render(path, axes):
    font = ImageFont.truetype(str(path), 220)
    try:
        names = [a["name"] if isinstance(a["name"], str) else a["name"].decode() for a in font.get_variation_axes()]
        vals = [a["default"] for a in font.get_variation_axes()]
        for k, v in axes.items():
            if k in names: vals[names.index(k)] = v
        font.set_variation_by_axes(vals)
    except OSError:
        names = []
    im = Image.new("L", (int(font.getlength(text)) + 200, 500), 0)
    ImageDraw.Draw(im).text((100, 100), text, 255, font=font)
    ink = tight(np.asarray(im, float) / 255)
    ratio = (ink.shape[1] / ink.shape[0]) / (W / H)
    scaled = np.asarray(Image.fromarray((ink * 255).astype("uint8")).resize((W, H), Image.LANCZOS), float) / 255
    iou = np.minimum(scaled, ref).sum() / np.maximum(scaled, ref).sum()
    return iou, ratio, names

results = []
for path in sorted(fonts_dir.glob("*.ttf")):
    if (path.stem in SANS) != (kind == "sans"):
        continue
    for wght in range(300, 801, 50):
        for opsz in ("Optical Size", None):
            for size in ((72, 144, 32, 14, 8) if opsz else (None,)):
                axes = {"Weight": wght}
                if size: axes["Optical Size"] = size
                try:
                    iou, ratio, names = render(path, axes)
                except Exception:
                    continue
                if size and "Optical Size" not in names: continue
                results.append((iou, path.stem, wght, size, ratio))
best = {}
for r in sorted(results, key=lambda r: r[0], reverse=True):
    best.setdefault(r[1], r)
for iou, name, wght, size, ratio in sorted(best.values(), key=lambda r: r[0], reverse=True):
    print(f"{name:20s} IoU {iou:.3f}  wght {wght}  opsz {size}  width {ratio:.3f}")
