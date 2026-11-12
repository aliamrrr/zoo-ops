# Reference film, measured

A second, deeper pass on the reference launch film, this time from numbers. Everything marked
*measured* comes from [tools/analyze_reference.py](tools/analyze_reference.py) (per frame activity,
palette, audio) and [tools/match_font.py](tools/match_font.py), run on the 1280x720 source.
Lengths are given at 720p, with the 1080p value we use in brackets (x1.5). Anything not marked
*measured* (zoom factors, blur radii, drift speeds, tile sizes) is an estimate read off enlarged
frames, good to about 20 %.

[MOTION_PLAYBOOK.md](MOTION_PLAYBOOK.md) is the summary. This file is the evidence, and the spec
for [src/film2.js](src/film2.js), which rebuilds the same grammar for Zoo Ops.

## 1. File and global numbers (measured)

| | |
| --- | --- |
| Container | 1280x720, 24 fps, 1386 frames, 57.75 s, H.264 about 650 kb/s |
| Frames with motion | 90.7 %. Only five holds of 8 to 10 identical frames in the whole film |
| Longest stillness | 0.42 s. The film is never frozen long enough to notice |
| Hard cuts | One, the last frame to black at 56.5 s. Every other change is a move of 4 to 7 frames |
| Audio | UI sounds only until 15.5 s, music from 15.5 s to 52 s, quiet under the logo |
| Tempo | About 92 bpm, so one beat is 0.65 s and about 16 frames |

The activity curve (mean pixel change per second) climbs through the film: under 1 in the cold
open, 2 to 5 in the first demo, 5 to 8 between 35 s and 47 s, then near zero for the tagline and
logo. Energy is spent in the middle and the end is calm.

## 2. Palette (measured)

| Role | Value |
| --- | --- |
| Background | `#FAF8F4`, on 77 % of frames |
| Dashboard background | `#FEF6EB`, a warmer cream used only inside the third demo |
| Ink | `#1A1A18` range, never `#000` |
| Selected text highlight | `#A9C7D0`, a dusty blue-grey |
| Neutral chip ("New in") | fill about `#EEECE4`, 1 px border about `#DCD9CE`, 6 px radius |
| Chat bubble | `#EFEEE9`, no border, 12 px radius [18] |
| Canvas grid | 1 px lines every 40 px [60], about 7 % ink |
| Cursor accents | terracotta, magenta, teal, blue, green: one per person, saturated, used on tiny areas |
| Icon accents | cobalt, rust, green, violet, crimson, plum, teal: one per product icon |

Color discipline: outside the demos, saturated color is confined to cursors, tags and icons, a
very small share of the frame. The demos carry their
own color (yellow sticky notes, green and pink cells), which is why the surrounding film stays
neutral.

## 3. Typography

**Serif (all headlines).** A proprietary house serif: sturdy, moderate contrast, large x-height,
ball terminals on a, c, f and r, tight tracking (about -2 %). It is not distributed, so it cannot
be used. We ranked 14 open-license serifs against the reference lettering:

| Candidate | Overlap on "Artifacts" | Width at equal height |
| --- | --- | --- |
| **Frank Ruhl Libre 500** | **0.657** | **1.002** |
| Gelasio 500 | 0.633 | 0.934 |
| STIX Two Text 500 | 0.630 | 0.977 |
| Newsreader 450 | 0.629 | 1.135 |
| Fraunces 550 | 0.606 | 0.973 |
| Source Serif 4 500 | 0.592 | 1.020 |

Frank Ruhl Libre matches width to 0.2 % and has the same color on the page. Film 2 uses it at
weights 400, 500 and 700 with `letter-spacing: -0.022em`.

**Sans (UI, chips, cursor tags).** A neutral grotesque, medium weight for chips, semibold white
on color for cursor tags. Film 2 uses Inter 400/500/600.

Sizes (measured on the frame):

| Element | 720p | 1080p |
| --- | --- | --- |
| Cold open word | 67 px ascender to baseline, 357 px wide, about 92 px font size | 140 |
| Chapter card, both lines | about 42 px font size. Line 1 regular, line 2 bold, leading 1.1 | 66 |
| Tagline | about 59 px font size, 750 px wide, one line | 88 |
| Chip text | 15 px | 23 |
| Cursor tag text | 11 to 12 px, semibold | 17 |
| Line icons | 22 px box, 2 px round stroke | 46 to 62 |

Headlines never exceed about 60 % of the frame width. The cold open word is only 28 % wide: small
type on a big empty field is a large part of the calm.

## 4. The moves, with their timings

Times in seconds, frame counts at 24 fps.

**Typing (0.71 to 1.46, measured).** First letter at frame 17. Then one letter every 2 frames
(12 letters per second), dead regular, except the last letter which waits 4 frames. The newest
letter is drawn in the caret's color for about 2 frames, then turns ink. The caret is a 3 px bar
[4] the height of the line, with the author's tag attached to its top right. The word is left
anchored at its final position, so nothing shifts when it completes.

**Caret to cursor (1.9 to 2.6).** After a 0.38 s hold (the first of the five holds), the caret
collapses into a small arrow with a tiny tag that drifts away down and left. The actor stays on
screen: it will "do" the next thing.

**Letter to icon morph (2.6 to 4.2).** Letters are removed left to right at about 0.12 s each
while icons appear from the left at about 0.15 s each. Each icon is *drawn* (its stroke grows
along the path) while it scales from roughly 55 % to 100 %. The icons are much smaller than the
letters, so a gap opens between the icon row and the remaining letters. At 4.5 the icons are wiped
right to left, 1 to 2 frames apart.

**Dragged type (4.9 to 6.5).** Line 1 enters at about 20 degrees, inside a thin rectangle in the
dragger's color with the dragger's tag centered on its lower edge. It travels on an arc for
about 1.25 s and rotates continuously, reaching level exactly as it stops (ease out, no
overshoot). Line 2 starts 0.65 s later (one beat) from the opposite side with the opposite tilt.
The rectangles vanish 2 frames after landing. The chapter icon is drawn on between the two
landings.

**Idle cursors (6.4 to 8.0).** Three cursors glide to rest around the title on soft arcs,
0.25 to 0.3 s apart. One tag turns into a rounded bubble and types a short reaction.

**Grid reveal (6.5 to 8.0).** The canvas grid appears line by line in random order, each line
growing from one end over about 0.5 s. It tells you the surface changed from "page" to "canvas"
without any cut.

**Slide aside (8.0 to 8.8).** The title is not removed: it scales up about 1.45x and slides to the
lower left until it is half cropped by the frame edge. The prompt card pops beside it. Elements are
allowed to leave the frame partially.

**Prompt card (8.3 to 10.3).** White card, hairline border, large soft shadow, small grey label,
an avatar disc outside its top left corner. An inline mention chip, then typed text, a ticked
checkbox row, and a round send button that is pressed (scale dip of about 10 % over 5 frames).

**Build on (10.5 to 22).** The result is assembled by a cursor: each element appears where the
cursor arrives. The camera drifts the whole time (scale creeping about 0.5 % per second).

**Whip (22.0 to 22.75, 37.2 to 37.9, 39.0 to 39.6, 41.9 to 42.4, measured).** The frame to frame
change ramps up almost linearly for 12 to 14 frames, then collapses within 2 frames. That is an
ease-in move on the outgoing layer that ends in the incoming layer already settled: old content
accelerates away, new content lands with a short ease out. Peak change is 12 to 16 on our scale,
against 2 to 4 for ordinary entrances.

**Focus pull (25.1 to 25.5).** Before the second demo the chapter title blurs (about 6 px [9])
while the chat bubble in front stays sharp, then the whole layer scrolls up. Blur is per layer,
used as depth of field, never as a full screen dissolve.

**Active cell (26 to 33).** In the sheet demo the working cell has a 2 px outline in the author's
color with the author's tag hanging from its corner. It jumps cell to cell. This is the same
"named actor" idea applied to data entry.

**Macro zoom (44.5 to 45.8).** The camera pushes about 3.4x onto one toolbar button with an
ease in out of about 0.85 s. The cursor is in the same space, so it scales too. Hover fill
arrives 5 to 7 frames before the click.

**Burst (46.75 to 49.3, measured spike at 46.75).** On the click, about 20 app tiles leave one
point, reach a loose ellipse within 0.8 s (strong ease out), keep drifting outward slowly, then
fly past the camera: they grow, blur and fade within 0.6 s, staggered randomly by up to 0.25 s.
Tile sizes vary from 0.55x to 1.3x to fake depth.

**Word swap (measured: 49.33, 50.00, 50.58, 51.17).** The highlight appears at 49.33, and the
word changes every 14 to 16 frames, on the beat. The swap is instant (no crossfade). The sentence
re-centers by a few pixels as the word width changes (text start moved from x 277 to 265 to 263
to 265). The highlight disappears at 51.79. The author's cursor sits at the lower right corner of
the highlight throughout.

**Reactions (51.8 to 53.4).** Other cursors arrive and small hearts, sparkles and stars pop
around the sentence, each drifting up.

**Logo (53.5 to 56.5).** The mark alone first, scaling and rotating in. Then it shifts left as the
wordmark is revealed beside it. About 2 s of hold with only a 1 % drift. Then black for 1.25 s.

## 5. Easing summary

| Move | Curve | Length |
| --- | --- | --- |
| Small things appearing (chips, tags, icons) | spring with about 5 % overshoot | 6 to 8 frames |
| Text and windows arriving | ease out (expo like), no overshoot | 12 to 30 frames |
| Leaving | ease in | 5 to 9 frames |
| Camera | ease in out | 20 to 30 frames |
| Cursor travel | ease in out on an arc | 15 to 22 frames |
| Typing | linear, 2 frames per letter | |
| Word swap, selection boxes off | instant | 1 frame |

## 6. What film 2 copies, and what it does not

Copied: background and ink values, the type system (closest open fonts), chips, cursor tags,
hairline cards, line icons drawn on, every move in section 4 with its measured timing, 24 fps, the
three chapter structure, the black ending.

Not copied: the reference's wordmark, logo, product names, people's names and its house color
(terracotta). Cursors are Zoo Ops keepers in their pattern colors, and the mark is the Owl. The
proprietary typefaces are replaced by Frank Ruhl Libre and Inter.
