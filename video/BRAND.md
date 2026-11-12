# Zoo Ops motion identity

Our own look for films. It borrows the *discipline* of the reference (see
[MOTION_PLAYBOOK.md](MOTION_PLAYBOOK.md)) and replaces every visible choice with one that comes from
the game. If a frame could be mistaken for the reference, it is wrong.

## What we changed, and why

| | Reference | Zoo Ops |
| --- | --- | --- |
| Mood | Calm, editorial, grown up | Playful, warm, a little cheeky |
| Background | Flat off-white, fine line grid | Cream paper `#fff8e8` with a slowly drifting dot grid |
| Headline type | High contrast serif | **Baloo 2** 800, round and chunky (the game's own font) |
| Body and code | Neutral grotesque | **Nunito** 800 for labels, **JetBrains Mono** for code |
| Ink | Near black | Plum `#4b3757` for all text and outlines |
| Surfaces | Hairline border, soft blurred shadow | **Sticker**: 4 to 6 px plum outline, hard offset shadow, big radius |
| Actors | Anonymous arrows with human names | **Keeper cursors**: the animal's face in the tag, in its pattern color |
| Entrances | Smooth ease out, almost no bounce | **Pop**: a spring with about 11 % overshoot, plus a small tilt |
| Layout | Perfectly level | Stickers sit 2 to 5 degrees off level, never the main headline |
| Color | Neutrals plus thin accents | Ten saturated pattern colors on cream, used as fills |
| Selection box | Thin solid rectangle | Dashed rectangle with square handles |
| Rewards | Emoji reactions | Coins, a burst ring, an animal hopping |
| Ending | Logo on off-white, then black | Owl, wordmark, the run command, the whole cast peeking in |

## Tokens

All in [src/style.css](src/style.css).

```
--paper   #fff8e8   background
--ink     #4b3757   text, outlines
--muted   #7d6c8c   secondary text
--faint   #b9aec4   asleep, disabled
--card    #ffffff   sticker fill
--green   #58c96c   success, primary     --green-dark #3a9a50
--pink    #ff8fab   caret, slow
--red     #e5484d   broken, costly
--yellow  #ffc93c   coins, highlight
--shadow  rgb(75 55 87 / 22%)   always hard: 0 7px 0
```

Pattern colors, one per level, always the same:

| 01 Cache | 02 Rate limit | 03 Reliability | 04 Idempotency | 05 Observability |
| --- | --- | --- | --- | --- |
| `#d9822b` | `#2f8fd6` | `#e2603a` | `#7a62d9` | `#159e8c` |

| 06 DB speed | 07 Integrity | 08 Async | 09 Auth | 10 Deploy |
| --- | --- | --- | --- | --- |
| `#8a6a4a` | `#d9538a` | `#b0483f` | `#3f5fae` | `#6c9a1f` |

A tint of a pattern color is `color-mix(in srgb, <color> 24%, white)`.

## Type scale (1920x1080)

| Class | Size | Use |
| --- | --- | --- |
| `.h-xl` | 168 / 800 | The one word of a cold open |
| `.h-lg` | 150 / 800 | Second line of a two line card |
| `.h-md` | 96 / 700 | First line of a two line card |
| `.h-sm` | 84 / 800 | Scene titles |
| `.h-xs` | 60 / 800 | Captions next to a big number |
| `.pill` | 34 / 700 | Every label that sits on a sticker |
| `.label` | 30 Nunito 800 | Quiet captions |
| code | 27 / 45 JetBrains Mono | Editor |

## Components

- **Pill**: white, plum outline, hard shadow. Variants `.bad` (red), `.good` (green), `.dark`.
  A `.num` chip at its left carries a level number in the pattern color.
- **Card**: same sticker treatment at 30 px radius. Editor, diagram nodes and pattern badges.
- **Keeper cursor**: chunky arrow plus a tag with the animal's face and name.
- **Critter**: any of the game's animals, full body or head shot, with `eyes` set to `open`,
  `blink`, `happy`, `asleep`, `sad`, `sick`.
- **Asleep and awake**: asleep is grey fill, dashed faint outline, closed eyes, "z z z", caution
  tape. Awake is white fill, solid plum outline, pattern color, a hop. This contrast is the story of
  the game, so every film should use it at least once.
- **Game window**: captured gameplay with a 6 px outline and 34 px radius.
- **Tech logos**: Redis, PostgreSQL, FastAPI and Python from Simple Icons, in their brand colors,
  always inside a card. They are other people's trademarks: use them to name the technology, never
  as decoration and never recolored.

## Motion rules

1. Things **pop** (`spring`) when they are small, and **glide** (`E.outExpo`, `E.inOut`) when they
   are big. A window never bounces, a pill always does.
2. Stickers land tilted and keep a tiny idle wobble. Headlines are level.
3. A state change is celebrated physically: burst ring, coins with gravity, a hop with squash.
4. Animals are alive: they blink on their own offsets and bob slowly.
5. One number per scene carries the argument (30, then 6). It is the biggest thing on screen.
6. Scene changes use the blur push: 0.3 s, blur to 18 px, scale to 105 %.
7. Text stays short: lowercase pills, no sentence longer than about seven words.

## Voice

Concrete and a bit dry. Say what happens in the zoo, then what it means in the backend.
"Hazel is asleep." "30 Owl calls for 6 questions." No hype words.
