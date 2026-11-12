# Motion playbook

How the reference product film is built, shot by shot, and the reusable craft we take from it.
The reference is a 57.8 s launch film (1280x720, 24 fps, H.264, music bed around -17 dB mean).
We study its **form** only. Our own look is in [BRAND.md](BRAND.md), and the film we made with it
is in [src/film.js](src/film.js).

The measured, frame accurate version of this analysis (palette, type sizes, typing cadence,
transition curves, tempo) is in [REFERENCE_ANALYSIS.md](REFERENCE_ANALYSIS.md). It is the spec for
[src/film2.js](src/film2.js), a second film that follows the reference's grammar closely
(`node render.mjs --film film2`).

## 1. What makes it feel premium, in one paragraph

Almost nothing is on screen at any moment. One warm off-white background, one typeface family,
one accent color per actor. Every element arrives by being *made* in front of you (typed, dragged,
drawn) by a visible actor (a named cursor), never by a plain fade. The camera never cuts: it pushes
into the UI, and the next scene grows out of the last one. Real product UI is shown, but always
simplified, enlarged, and isolated on the same background, so the film reads as one continuous
surface.

## 2. Structure and pacing

| Time | Beat | What happens | Length |
| --- | --- | --- | --- |
| 0.0 | Cold open | Tiny tag pops, a caret types the product word | 2.5 s |
| 2.5 | Morph | The word's letters are replaced one by one by small icons (the product family) | 2.5 s |
| 5.0 | Chapter card 1 | Two lines of type fly in, held by cursors, and snap straight | 3 s |
| 8.0 | Demo 1 | A prompt is typed in a small card, the result builds itself piece by piece | 12 s |
| 20.0 | Chapter card 2 | Same card layout, different icon and color | 3 s |
| 23.0 | Demo 2 | Blur push through the card into a full app window, cells fill in | 10 s |
| 33.0 | Chapter card 3 | Same again | 2 s |
| 35.0 | Demo 3 | Dashboard assembles, then a restyle, then scroll | 9 s |
| 44.0 | Detail | Extreme zoom on one button, a big arrow cursor clicks it | 3 s |
| 47.0 | Ecosystem | A cloud of app icons flies outward from the click | 2.5 s |
| 49.5 | Tagline | One sentence, its first word swaps 4 times in a highlight | 4 s |
| 53.5 | Logo | Mark and wordmark, hold | 3 s |
| 56.5 | Black | Hard end | 1.3 s |

Rules we keep:

- **Rule of three, then a payoff.** Three chapters built on one template, so the viewer learns the
  rhythm by the second one and the third can be shorter.
- **Chapter cards are 2 to 3 s**, demos 9 to 12 s. Nothing static lasts more than about 1.2 s.
- **Shots get shorter toward the end.** The last 10 s holds four ideas.
- **About 12 words on screen at once, maximum.** Chapter cards are 4 to 5 words in two lines, with
  the second line heavier than the first.
- **The demo content tells one small story** (one fictional company, same data across all demos),
  so no shot needs explaining.

## 3. Visual system of the reference

- **Background**: warm off-white, around `#F8F7F3`. A faint 1 px grid fades in *only* when a canvas
  type surface is on screen, drawn line by line from one corner.
- **Type**: one high contrast transitional serif for every headline (regular for line 1, semibold
  for line 2, tight leading, about 6 % of frame height), one neutral grotesque for UI and labels.
  Near black `#1A1A19`, never pure black.
- **Color**: neutrals carry the frame. Color only appears as (a) one accent per collaborator cursor
  (terracotta, magenta, teal, blue) and (b) one accent per product icon. A pale blue-grey highlight
  marks selected text.
- **Surfaces**: white cards, 1 px hairline border, very soft large shadow, 10 to 14 px radius.
- **Icons**: thin 1.5 px line icons, each in its own color, small (about 3 % of frame height).

## 4. The animation vocabulary

Each of these is a reusable move. Names are ours.

1. **Caret typing.** Text is left anchored and typed by a colored caret with a name tag riding on
   top. The newest character is tinted with the caret color for a frame or two before going dark.
   About 12 characters per second for headlines, faster for body copy.
2. **Named cursors as actors.** A small arrow with a rounded name tag. It always moves on a curve,
   eases out when arriving, and something happens *where it arrives*. Several cursors on screen
   means "collaboration" without a word of copy.
3. **Letter to icon morph.** The headline is replaced left to right: each letter shrinks out while
   an icon scales in at its place, staggered about 3 frames apart. The remaining letters stay put,
   so mid transition you read half word, half icons.
4. **Dragged type.** A line of text enters tilted 10 to 20 degrees inside a thin selection
   rectangle, pulled by a cursor, and rotates to level as it lands. The selection box fades a few
   frames after release. Two lines arrive from opposite sides, 6 to 8 frames apart.
5. **Build on.** Complex results are never revealed whole. A timeline grows node by node along its
   path, a sheet fills cell by cell with the active cell outlined, a chart draws its line left to
   right. The camera drifts slowly while it happens.
6. **Blur push.** To change scene, the current layer blurs (about 12 px) and scales up slightly
   while the next one slides in sharp from below or from the side. It reads as depth of field, not
   as a dissolve.
7. **Camera push in.** UI starts small and centered, then the camera goes to 3 to 4 times scale on
   one control, so a 24 px button fills a third of the frame. The cursor is scaled with it.
8. **Hover then click.** The button gets its hover fill 4 to 6 frames before the click, and the
   click triggers the next scene.
9. **Radial burst.** Many small tiles fly out from one point with different speeds and settle on
   a loose ring, then continue past the camera (they blur as they get close).
10. **Word swap.** A fixed sentence where one word, in a highlight box, is replaced several times
    at a steady beat (about 0.75 s each). The sentence re centers as the word width changes.
11. **Reactions.** Tiny emoji hearts and sparkles pop around the last headline, each from a cursor.
12. **Logo resolve.** Everything clears, the mark alone, then mark plus wordmark, long hold.

Timing and easing observed:

- Entrances: 8 to 12 frames at 24 fps (0.35 to 0.5 s), strong ease out (expo like), no bounce on
  large objects, a small overshoot (about 5 %) on tags and icons only.
- Exits: shorter than entrances, 5 to 7 frames, ease in.
- Stagger: 2 to 3 frames between siblings.
- Camera moves: 18 to 24 frames, ease in out.
- Something always moves slowly (camera drift, a cursor idling) so holds never freeze.

## 5. Editing and sound

- No hard cuts until the very last frame. Scene changes are blur pushes, zooms, or a shared element
  that stays on screen (the chapter title slides left and stays while the demo opens beside it).
- The music is a light rhythmic bed. Typing, pops and clicks land on the beat, and the tagline word
  swaps are exactly on consecutive beats. Decide the tempo first, then place keyframes on it.
- Ending on 1 s of black gives the logo a clean out.

## 6. How we build films like this

The stack is plain web technology, rendered offline:

- **One HTML page, 1920x1080.** Every element is absolutely positioned on that stage.
- **Time is the only input.** `seek(t)` computes every style from `t`. No CSS animations, no
  `setTimeout`. Any frame can be rendered alone, in any order, and always looks the same.
- **Scenes** are `scene(start, end, build)`. `build` creates the DOM once and returns `update(t)`.
  Scenes overlap by 0.2 s so the blur push out of one covers the fade in of the next.
- **Rendering**: [render.mjs](render.mjs) drives headless Chrome with `puppeteer-core`, calls
  `seek(i / fps)`, screenshots, and pipes the frames to `ffmpeg` (libx264, CRF 15, yuv420p).
- **Real product footage**: [capture-game.mjs](capture-game.mjs) records the running game through
  Chrome's screencast into a timestamped JPEG sequence, which the film plays back by time.
- **Characters** are drawn by the game's own module (`zoo/static/js/art.js`), so the film can never
  drift from the game.

The primitives, all in [src/kit.js](src/kit.js):

| Helper | Use |
| --- | --- |
| `p(t, t0, d, ease)` | Progress 0..1 of a tween. The building block of everything. |
| `spring(t, t0)` | The "pop": damped spring with about 11 % overshoot, settles in 0.45 s. |
| `pop(t, in, out)` | Pop in, then shrink and fade out. Returns `{s, o}`. |
| `put(el, {x, y, s, r, o, blur})` | Place an element by its center on the stage. |
| `typing(text)` + `typedCount` | Humanized, deterministic typing (pauses after punctuation and new lines, instant auto indent). |
| `textWidth(text, font)` | Measure text to drive carets and word swaps. |
| `critter(parent, kind, size)` | A game animal on a canvas, redrawn each frame (blink, hop, sleep). |
| `cursor(parent, kind, name, color)` | A keeper cursor with its name tag. |
| `clipWindow(parent, clip, width)` | Captured gameplay in a window, `show(time)`. |

Commands:

```
cd video
npm install
npm run preview                      # live preview, space = pause, arrows = scrub
node render.mjs --still 26.8         # one frame as PNG
node render.mjs --sheet 5,10,15,20   # contact sheet, the fastest way to review a change
node render.mjs --from 17 --to 31    # one section
npm run render                       # the full film, out/zoo-ops.mp4
```

To re record the gameplay clips: run `python -m zoo play --no-browser --port 8765`, then
`node capture-game.mjs http://127.0.0.1:8765 before 14` (and `after` on a checkout where level 1
passes).

## 7. Checklist before rendering

- Read the film as a contact sheet at 1 frame per second: is each frame understandable alone?
- No more than about 12 words on screen. One idea per shot.
- Every element enters through an action (typed, popped, dragged, drawn). No bare fades.
- Nothing is static for more than about 1.2 s.
- Entrances are longer than exits. Siblings are staggered.
- Each scene hands something to the next (a shared element, a zoom target, a blur push).
- Numbers on screen are true to the product.
- The last frame works as a thumbnail.
