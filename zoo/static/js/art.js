/**
 * The drawing kit: soft vector shapes, the animal cast and small icons, all on a 2D canvas.
 * Every animal shares one chubby template (big head, small body, sticker outline) and differs
 * by a spec: colors, ears, tail, beak and a few extras.
 */

const TAU = Math.PI * 2;
export const OUTLINE = "#4b3757";
export const FONT = '"Baloo 2", "Nunito", system-ui, sans-serif';
const EYE = "#2b2233";

function paint(ctx, fill, stroke, lw) {
  if (fill) {
    ctx.fillStyle = fill;
    ctx.fill();
  }
  if (stroke) {
    ctx.strokeStyle = stroke;
    ctx.lineWidth = lw;
    ctx.stroke();
  }
}

export function oval(ctx, x, y, rx, ry, fill, stroke = null, lw = 2, rot = 0) {
  ctx.beginPath();
  ctx.ellipse(x, y, Math.max(0, rx), Math.max(0, ry), rot, 0, TAU);
  paint(ctx, fill, stroke, lw);
}

export function rrect(ctx, x, y, w, h, r, fill, stroke = null, lw = 2) {
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
  paint(ctx, fill, stroke, lw);
}

/** Closed polygon from a flat [x0, y0, x1, y1, ...] list. */
export function poly(ctx, points, fill, stroke = null, lw = 2) {
  ctx.beginPath();
  ctx.moveTo(points[0], points[1]);
  for (let i = 2; i < points.length; i += 2) ctx.lineTo(points[i], points[i + 1]);
  ctx.closePath();
  paint(ctx, fill, stroke, lw);
}

export function line(ctx, points, stroke, lw = 2) {
  ctx.beginPath();
  ctx.moveTo(points[0], points[1]);
  for (let i = 2; i < points.length; i += 2) ctx.lineTo(points[i], points[i + 1]);
  ctx.strokeStyle = stroke;
  ctx.lineWidth = lw;
  ctx.lineCap = "round";
  ctx.stroke();
}

export function mix(a, b, k) {
  const pa = Number.parseInt(a.slice(1), 16);
  const pb = Number.parseInt(b.slice(1), 16);
  const channel = (shift) =>
    Math.round(((pa >> shift) & 255) + (((pb >> shift) & 255) - ((pa >> shift) & 255)) * k);
  return `rgb(${channel(16)},${channel(8)},${channel(0)})`;
}

/* The cast */

const SPECS = {
  owl: { body: "#a8754f", belly: "#f6e3c2", ears: "tuft", beak: "owl", wings: "#8a5d3d",
    discs: "#f6e3c2", eye: 0.056 },
  squirrel: { body: "#dc8a45", belly: "#fde9c9", ears: "point", earIn: "#f4b48a", tail: "curl",
    tailColor: "#c66f2e", muzzle: "#fde9c9" },
  goose: { body: "#ffffff", belly: "#eef3fa", beak: "wide", wings: "#e3ebf6", feet: "#f29a3a",
    hat: "cap" },
  fox: { body: "#ee8a3c", belly: "#fff4e3", ears: "point", earIn: "#6b4040", tail: "bushy",
    tailColor: "#ee8a3c", muzzle: "#fff4e3" },
  cat: { body: "#a7b0c6", belly: "#eef1f7", ears: "point", earIn: "#f7b6c6", tail: "thin",
    muzzle: "#eef1f7", whiskers: true, stripes: "#8791ab" },
  meerkat: { body: "#e0bb8a", belly: "#f6e6c9", ears: "tiny", earColor: "#6b4b3a",
    patches: "#6b4b3a", tail: "thin" },
  mole: { body: "#7b748c", belly: "#9a93aa", nose: "#f59ab0", bigNose: true, hat: "hard",
    paws: "#f7b6c6", eye: 0.024 },
  beaver: { body: "#9a6a45", belly: "#d9b48a", ears: "round", tail: "flat", teeth: true,
    muzzle: "#d9b48a" },
  ant: { body: "#9a4f48", belly: "#b5655c", antennae: true },
  dog: { body: "#e3b06a", belly: "#fbe9c9", ears: "flop", earColor: "#9a6a45", patch: "#c98e52",
    collar: "#e2554f", tail: "wag", muzzle: "#fbe9c9" },
  canary: { body: "#ffd84d", belly: "#fff0a8", beak: "small", wings: "#f4b92e", crest: true,
    feet: "#f29a3a" },
  lion: { body: "#f3bf63", belly: "#fde9c0", ears: "round", mane: "#cf7c2c", tail: "tuft",
    muzzle: "#fde9c0" },
  otter: { body: "#93694c", belly: "#f0d9b8", ears: "tiny", muzzle: "#f0d9b8", whiskers: true,
    tail: "thick" },
  penguin: { body: "#3f4f73", belly: "#ffffff", beak: "small", wings: "#34425f", feet: "#f29a3a",
    face: "penguin" },
  hedgehog: { body: "#f3dcb8", belly: "#fbeedb", spikes: "#8f6b50", ears: "tiny" },
  rabbit: { body: "#fffaf5", belly: "#ffffff", ears: "long", earIn: "#f7b6c6", tail: "nub" },
  frog: { body: "#7fd06c", belly: "#d3f2b6", topEyes: true, wideMouth: true },
  pigeon: { body: "#a3b3c8", belly: "#c3cfde", beak: "small", wings: "#8496b0",
    neckPatch: "#7fbfae", feet: "#e2726a" },
  raccoon: { body: "#9399a8", belly: "#d5d9e2", ears: "point", earIn: "#5b6070", mask: "#454a5a",
    tail: "ring", muzzle: "#eceff4" },
  panda: { body: "#ffffff", belly: "#f1f1f6", ears: "round", earColor: "#3a3344",
    patches: "#3a3344", feet: "#3a3344", arms: "#3a3344", hat: "cap", capColor: "#58c96c" },
  parrot: { body: "#e5574f", belly: "#f28a7e", beak: "hook", wings: "#3f8fdc", face: "parrot",
    feet: "#8a8f9c", tail: "feather" },
};

export const KINDS = Object.keys(SPECS);

function tailStroke(ctx, u, lw, color, width, end, tip) {
  ctx.lineCap = "round";
  for (const [stroke, w] of [[OUTLINE, width + lw * 2], [color, width]]) {
    ctx.beginPath();
    ctx.moveTo(-0.18 * u, -0.12 * u);
    ctx.quadraticCurveTo(-0.52 * u, -0.1 * u, end[0] * u, end[1] * u);
    ctx.strokeStyle = stroke;
    ctx.lineWidth = w;
    ctx.stroke();
  }
  if (tip) oval(ctx, end[0] * u, end[1] * u, 0.07 * u, 0.07 * u, tip, OUTLINE, lw);
}

function drawTail(ctx, spec, u, lw, c, time) {
  const color = c(spec.tailColor || spec.body);
  switch (spec.tail) {
    case "curl":
      oval(ctx, -0.3 * u, -0.5 * u, 0.15 * u, 0.27 * u, color, OUTLINE, lw, -0.25);
      oval(ctx, -0.32 * u, -0.54 * u, 0.06 * u, 0.16 * u, c("#e9a15c"), null, 0, -0.25);
      break;
    case "bushy":
    case "ring":
      oval(ctx, -0.33 * u, -0.2 * u, 0.2 * u, 0.1 * u, color, OUTLINE, lw, 0.5);
      if (spec.tail === "ring") {
        line(ctx, [-0.3 * u, -0.27 * u, -0.25 * u, -0.13 * u], c(spec.mask), 0.05 * u);
        line(ctx, [-0.4 * u, -0.32 * u, -0.35 * u, -0.19 * u], c(spec.mask), 0.05 * u);
      } else {
        oval(ctx, -0.46 * u, -0.28 * u, 0.075 * u, 0.065 * u, "#fff", OUTLINE, lw);
      }
      break;
    case "thin":
      tailStroke(ctx, u, lw, color, 0.055 * u, [-0.42, -0.46], null);
      break;
    case "thick":
      tailStroke(ctx, u, lw, color, 0.1 * u, [-0.44, -0.3], null);
      break;
    case "tuft":
      tailStroke(ctx, u, lw, color, 0.05 * u, [-0.44, -0.44], c(spec.mane));
      break;
    case "wag": {
      const swing = Math.sin(time * 14) * 0.08;
      tailStroke(ctx, u, lw, color, 0.06 * u, [-0.36 + swing, -0.42], null);
      break;
    }
    case "flat":
      oval(ctx, -0.34 * u, -0.07 * u, 0.17 * u, 0.075 * u, c("#6e4a30"), OUTLINE, lw, 0.2);
      break;
    case "nub":
      oval(ctx, -0.24 * u, -0.14 * u, 0.07 * u, 0.07 * u, "#fff", OUTLINE, lw);
      break;
    case "feather":
      poly(ctx, [-0.12 * u, -0.2 * u, -0.38 * u, 0.02 * u, -0.2 * u, -0.02 * u, -0.05 * u,
        -0.1 * u], c(spec.wings), OUTLINE, lw);
      break;
    default:
      if (spec.wings) {
        poly(ctx, [-0.16 * u, -0.26 * u, -0.38 * u, -0.14 * u, -0.16 * u, -0.1 * u],
          c(spec.wings), OUTLINE, lw);
      }
  }
}

function drawEars(ctx, spec, u, lw, c) {
  const color = c(spec.earColor || spec.body);
  const inner = spec.earIn ? c(spec.earIn) : null;
  for (const side of [-1, 1]) {
    switch (spec.ears) {
      case "round":
        oval(ctx, side * 0.22 * u, -0.84 * u, 0.085 * u, 0.085 * u, color, OUTLINE, lw);
        oval(ctx, side * 0.22 * u, -0.83 * u, 0.04 * u, 0.04 * u, c(spec.belly));
        break;
      case "point":
        poly(ctx, [side * 0.07 * u, -0.83 * u, side * 0.26 * u, -1.01 * u, side * 0.31 * u,
          -0.71 * u], color, OUTLINE, lw);
        if (inner) {
          poly(ctx, [side * 0.15 * u, -0.83 * u, side * 0.25 * u, -0.94 * u, side * 0.27 * u,
            -0.78 * u], inner);
        }
        break;
      case "long":
        oval(ctx, side * 0.1 * u, -1.04 * u, 0.065 * u, 0.2 * u, color, OUTLINE, lw, side * 0.14);
        oval(ctx, side * 0.1 * u, -1.04 * u, 0.03 * u, 0.14 * u, inner, null, 0, side * 0.14);
        break;
      case "tiny":
        oval(ctx, side * 0.24 * u, -0.8 * u, 0.05 * u, 0.05 * u, color, OUTLINE, lw);
        break;
      case "tuft":
        poly(ctx, [side * 0.1 * u, -0.85 * u, side * 0.28 * u, -0.99 * u, side * 0.27 * u,
          -0.75 * u], color, OUTLINE, lw);
        break;
      default:
    }
    if (spec.antennae) {
      line(ctx, [side * 0.08 * u, -0.86 * u, side * 0.17 * u, -1.04 * u], OUTLINE, lw);
      oval(ctx, side * 0.17 * u, -1.05 * u, 0.035 * u, 0.035 * u, color, OUTLINE, lw * 0.8);
    }
    if (spec.topEyes) {
      oval(ctx, side * 0.14 * u, -0.85 * u, 0.1 * u, 0.1 * u, color, OUTLINE, lw);
    }
  }
}

function drawEye(ctx, x, y, r, mode, lw, side) {
  ctx.lineCap = "round";
  ctx.strokeStyle = EYE;
  ctx.lineWidth = lw;
  if (mode === "blink" || mode === "asleep") {
    ctx.beginPath();
    ctx.arc(x, y - r * 0.3, r, 0.15 * Math.PI, 0.85 * Math.PI);
    ctx.stroke();
    return;
  }
  if (mode === "happy") {
    ctx.beginPath();
    ctx.arc(x, y + r * 0.5, r, 1.15 * Math.PI, 1.85 * Math.PI);
    ctx.stroke();
    return;
  }
  if (mode === "sick") {
    line(ctx, [x - r, y - r, x + r, y + r], EYE, lw);
    line(ctx, [x - r, y + r, x + r, y - r], EYE, lw);
    return;
  }
  oval(ctx, x, y, r, r * 1.25, EYE);
  oval(ctx, x - r * 0.3, y - r * 0.45, r * 0.38, r * 0.38, "#fff");
  if (mode === "angry") {
    line(ctx, [x + side * r * 1.5, y - r * 2.3, x - side * r * 1.1, y - r * 1.4], EYE, lw * 1.2);
  } else if (mode === "sad") {
    line(ctx, [x + side * r * 1.5, y - r * 1.5, x - side * r * 1.1, y - r * 2.2], EYE, lw);
    oval(ctx, x + side * r * 0.9, y + r * 2.2, r * 0.45, r * 0.7, "#6cc5f2");
  }
}

function drawFaceParts(ctx, spec, u, lw, c, eyes) {
  if (spec.face === "penguin") {
    oval(ctx, -0.1 * u, -0.62 * u, 0.13 * u, 0.15 * u, "#fff");
    oval(ctx, 0.1 * u, -0.62 * u, 0.13 * u, 0.15 * u, "#fff");
    oval(ctx, 0, -0.54 * u, 0.17 * u, 0.11 * u, "#fff");
  }
  if (spec.face === "parrot") oval(ctx, 0, -0.63 * u, 0.2 * u, 0.13 * u, c("#fff7ec"));
  if (spec.muzzle) oval(ctx, 0, -0.53 * u, 0.15 * u, 0.1 * u, c(spec.muzzle));
  if (spec.discs) {
    const rim = mix(spec.body, "#000000", 0.18);
    oval(ctx, -0.12 * u, -0.64 * u, 0.125 * u, 0.125 * u, c(spec.discs), rim, lw * 0.6);
    oval(ctx, 0.12 * u, -0.64 * u, 0.125 * u, 0.125 * u, c(spec.discs), rim, lw * 0.6);
  }
  if (spec.mask) {
    oval(ctx, -0.12 * u, -0.64 * u, 0.1 * u, 0.075 * u, c(spec.mask), null, 0, 0.3);
    oval(ctx, 0.12 * u, -0.64 * u, 0.1 * u, 0.075 * u, c(spec.mask), null, 0, -0.3);
  }
  if (spec.patches) {
    oval(ctx, -0.115 * u, -0.64 * u, 0.06 * u, 0.068 * u, c(spec.patches));
    oval(ctx, 0.115 * u, -0.64 * u, 0.06 * u, 0.068 * u, c(spec.patches));
  }
  if (spec.patch) oval(ctx, 0.125 * u, -0.65 * u, 0.1 * u, 0.11 * u, c(spec.patch));
  if (spec.stripes) {
    for (const x of [-0.07, 0, 0.07]) {
      line(ctx, [x * u, -0.87 * u, x * u, -0.8 * u], c(spec.stripes), lw);
    }
  }

  const ex = (spec.discs ? 0.12 : 0.115) * u;
  const ey = (spec.topEyes ? -0.86 : -0.64) * u;
  const er = (spec.eye || 0.042) * u;
  const light = spec.mask || spec.patches;
  if (light && eyes !== "sick" && eyes !== "blink" && eyes !== "asleep" && eyes !== "happy") {
    oval(ctx, -ex, ey, er * 1.25, er * 1.5, "#fff");
    oval(ctx, ex, ey, er * 1.25, er * 1.5, "#fff");
  }
  drawEye(ctx, -ex, ey, er, eyes, lw, -1);
  drawEye(ctx, ex, ey, er, eyes, lw, 1);
  if (eyes !== "sick") {
    oval(ctx, -0.215 * u, -0.545 * u, 0.055 * u, 0.032 * u, "rgba(255,120,150,0.5)");
    oval(ctx, 0.215 * u, -0.545 * u, 0.055 * u, 0.032 * u, "rgba(255,120,150,0.5)");
  }

  switch (spec.beak) {
    case "small":
      poly(ctx, [-0.05 * u, -0.575 * u, 0.05 * u, -0.575 * u, 0, -0.5 * u], "#f29a3a", OUTLINE,
        lw * 0.8);
      break;
    case "wide":
      oval(ctx, 0, -0.54 * u, 0.115 * u, 0.052 * u, "#f29a3a", OUTLINE, lw);
      line(ctx, [-0.07 * u, -0.54 * u, 0.07 * u, -0.54 * u], "#c9772a", lw * 0.6);
      break;
    case "hook":
      oval(ctx, 0, -0.55 * u, 0.07 * u, 0.09 * u, "#ffe7b8", OUTLINE, lw);
      oval(ctx, 0, -0.49 * u, 0.035 * u, 0.035 * u, "#5a4a4a");
      break;
    case "owl":
      poly(ctx, [-0.04 * u, -0.6 * u, 0.04 * u, -0.6 * u, 0, -0.52 * u], "#f2a23a", OUTLINE,
        lw * 0.8);
      break;
    default:
      if (spec.wideMouth) {
        ctx.beginPath();
        ctx.arc(0, -0.66 * u, 0.17 * u, 0.2 * Math.PI, 0.8 * Math.PI);
        ctx.strokeStyle = EYE;
        ctx.lineWidth = lw;
        ctx.stroke();
      } else if (!spec.antennae) {
        const big = spec.bigNose;
        oval(ctx, 0, -0.575 * u, (big ? 0.06 : 0.032) * u, (big ? 0.045 : 0.024) * u,
          c(spec.nose || "#3a2a3a"), big ? OUTLINE : null, lw * 0.7);
        if (!big && !spec.teeth) {
          ctx.strokeStyle = EYE;
          ctx.lineWidth = lw * 0.7;
          for (const side of [-1, 1]) {
            ctx.beginPath();
            ctx.arc(side * 0.03 * u, -0.548 * u, 0.03 * u, 0.1 * Math.PI, 0.9 * Math.PI);
            ctx.stroke();
          }
        }
      } else {
        ctx.beginPath();
        ctx.arc(0, -0.58 * u, 0.05 * u, 0.15 * Math.PI, 0.85 * Math.PI);
        ctx.strokeStyle = EYE;
        ctx.lineWidth = lw * 0.8;
        ctx.stroke();
      }
  }
  if (spec.teeth) rrect(ctx, -0.04 * u, -0.55 * u, 0.08 * u, 0.055 * u, 0.012 * u, "#fff", OUTLINE, lw * 0.6);
  if (spec.whiskers) {
    for (const side of [-1, 1]) {
      line(ctx, [side * 0.14 * u, -0.55 * u, side * 0.3 * u, -0.58 * u], "rgba(60,45,70,0.55)",
        lw * 0.45);
      line(ctx, [side * 0.14 * u, -0.53 * u, side * 0.3 * u, -0.5 * u], "rgba(60,45,70,0.55)",
        lw * 0.45);
    }
  }
}

/**
 * Draw one animal standing at (x, y), y being the ground under its feet, `s` its height.
 * Options: flip, squash (-0.2..0.2), eyes (open, blink, happy, asleep, sick, angry, sad),
 * flap (0..1 for wings), lift (pixels above the ground), time, shadow, carry(ctx, u).
 */
export function drawCritter(ctx, kind, x, y, s, options = {}) {
  const spec = SPECS[kind];
  const { flip = false, squash = 0, eyes = "open", time = 0, shadow = true, flap = 0, lift = 0,
    carry = null } = options;
  const u = s;
  const lw = Math.max(1.3, s * 0.036);
  const sick = eyes === "sick";
  const c = (hex) => (sick ? mix(hex, "#a6d86a", 0.45) : hex);

  if (shadow) {
    const shrink = 1 / (1 + lift / 60);
    oval(ctx, x, y + s * 0.01, s * 0.3 * shrink, s * 0.085 * shrink, "rgba(45,60,80,0.2)");
  }
  ctx.save();
  ctx.translate(x, y - lift);
  ctx.scale((flip ? -1 : 1) * (1 + squash), 1 - squash);
  ctx.lineJoin = "round";

  if (spec.spikes) {
    const points = [];
    for (let i = 0; i <= 20; i += 1) {
      const angle = Math.PI * (0.82 + (i / 20) * 1.36);
      const radius = (i % 2 ? 0.52 : 0.41) * u;
      points.push(Math.cos(angle) * radius, -0.42 * u + Math.sin(angle) * radius);
    }
    poly(ctx, points, c(spec.spikes), OUTLINE, lw);
  }
  drawTail(ctx, spec, u, lw, c, time);

  const feet = c(spec.feet || mix(spec.body, "#000000", 0.14));
  oval(ctx, -0.11 * u, -0.02 * u, 0.085 * u, 0.05 * u, feet, OUTLINE, lw);
  oval(ctx, 0.11 * u, -0.02 * u, 0.085 * u, 0.05 * u, feet, OUTLINE, lw);
  oval(ctx, 0, -0.25 * u, 0.24 * u, 0.23 * u, c(spec.body), OUTLINE, lw);
  oval(ctx, 0, -0.2 * u, 0.15 * u, 0.15 * u, c(spec.belly));
  if (spec.neckPatch) oval(ctx, 0, -0.4 * u, 0.15 * u, 0.05 * u, c(spec.neckPatch));
  if (spec.collar) {
    rrect(ctx, -0.16 * u, -0.45 * u, 0.32 * u, 0.07 * u, 0.03 * u, spec.collar, OUTLINE, lw * 0.8);
    oval(ctx, 0, -0.37 * u, 0.035 * u, 0.035 * u, "#ffd23f", OUTLINE, lw * 0.6);
  }

  for (const side of [-1, 1]) {
    if (spec.wings) {
      oval(ctx, side * (0.24 + flap * 0.06) * u, (-0.29 - flap * 0.14) * u, 0.075 * u, 0.15 * u,
        c(spec.wings), OUTLINE, lw, side * (0.25 + flap * 1.3));
    } else if (spec.paws) {
      oval(ctx, side * 0.24 * u, -0.24 * u, 0.08 * u, 0.06 * u, spec.paws, OUTLINE, lw);
    } else {
      oval(ctx, side * 0.21 * u, -0.27 * u, 0.05 * u, 0.085 * u, c(spec.arms || spec.body), OUTLINE, lw,
        side * -0.45);
    }
  }
  if (carry) carry(ctx, u);

  if (spec.mane) {
    for (let i = 0; i < 11; i += 1) {
      const angle = (i / 11) * TAU;
      oval(ctx, Math.cos(angle) * 0.3 * u, -0.62 * u + Math.sin(angle) * 0.28 * u, 0.1 * u,
        0.1 * u, c(spec.mane), OUTLINE, lw);
    }
    oval(ctx, 0, -0.62 * u, 0.3 * u, 0.28 * u, c(spec.mane));
  }
  drawEars(ctx, spec, u, lw, c);
  oval(ctx, 0, -0.62 * u, 0.3 * u, 0.27 * u, c(spec.body), OUTLINE, lw);
  drawFaceParts(ctx, spec, u, lw, c, eyes);

  if (spec.ears === "flop") {
    for (const side of [-1, 1]) {
      oval(ctx, side * 0.29 * u, -0.65 * u, 0.08 * u, 0.16 * u, c(spec.earColor), OUTLINE, lw,
        side * -0.2);
    }
  }
  if (spec.crest) oval(ctx, 0.03 * u, -0.92 * u, 0.035 * u, 0.075 * u, spec.wings, OUTLINE, lw, 0.4);
  if (spec.hat === "hard") {
    ctx.beginPath();
    ctx.ellipse(0, -0.78 * u, 0.25 * u, 0.17 * u, 0, Math.PI, TAU);
    ctx.closePath();
    paint(ctx, "#ffd23f", OUTLINE, lw);
    rrect(ctx, -0.29 * u, -0.8 * u, 0.58 * u, 0.05 * u, 0.02 * u, "#ffd23f", OUTLINE, lw);
    oval(ctx, 0, -0.89 * u, 0.045 * u, 0.035 * u, "#fff6c9", OUTLINE, lw * 0.7);
  }
  if (spec.hat === "cap") {
    ctx.beginPath();
    ctx.ellipse(0, -0.8 * u, 0.2 * u, 0.13 * u, 0, Math.PI, TAU);
    ctx.closePath();
    const cap = spec.capColor || "#4a7fd6";
    paint(ctx, cap, OUTLINE, lw);
    rrect(ctx, -0.02 * u, -0.83 * u, 0.3 * u, 0.045 * u, 0.02 * u, mix(cap, "#000000", 0.2), OUTLINE, lw);
    oval(ctx, 0, -0.86 * u, 0.03 * u, 0.03 * u, "#ffd23f");
  }
  ctx.restore();
}

/** A standalone canvas with one animal, for the page chrome (cards, dock, overlays). */
export function critterCanvas(kind, size, options = {}) {
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  const canvas = document.createElement("canvas");
  const { face = false } = options;
  canvas.width = Math.round(size * ratio);
  canvas.height = Math.round(size * ratio);
  canvas.style.width = `${size}px`;
  canvas.style.height = `${size}px`;
  canvas.dataset.kind = kind;
  paintCritterCanvas(canvas, kind, { face, eyes: options.eyes || "open" });
  return canvas;
}

export function paintCritterCanvas(canvas, kind, { face = false, eyes = "open" } = {}) {
  const ctx = canvas.getContext("2d");
  const size = canvas.width;
  ctx.clearRect(0, 0, size, size);
  if (face) drawCritter(ctx, kind, size / 2, size * 1.28, size * 1.42, { eyes, shadow: false });
  else drawCritter(ctx, kind, size / 2, size * 0.93, size * 0.84, { eyes });
}

/* Icons and emotes */

export function heart(ctx, x, y, r, color = "#ff6b8f") {
  ctx.beginPath();
  ctx.moveTo(x, y + r * 0.9);
  ctx.bezierCurveTo(x - r * 1.6, y - r * 0.2, x - r * 0.7, y - r * 1.3, x, y - r * 0.45);
  ctx.bezierCurveTo(x + r * 0.7, y - r * 1.3, x + r * 1.6, y - r * 0.2, x, y + r * 0.9);
  ctx.fillStyle = color;
  ctx.fill();
}

export function star(ctx, x, y, r, color, inner = 0.45, points = 5, rotation = -Math.PI / 2) {
  ctx.beginPath();
  for (let i = 0; i < points * 2; i += 1) {
    const radius = i % 2 ? r * inner : r;
    const angle = rotation + (i / (points * 2)) * TAU;
    ctx.lineTo(x + Math.cos(angle) * radius, y + Math.sin(angle) * radius);
  }
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
}

export function sparkle(ctx, x, y, r, color) {
  star(ctx, x, y, r, color, 0.28, 4);
}

export function coin(ctx, x, y, r) {
  oval(ctx, x, y, r, r, "#ffc93c", "#b8791a", Math.max(1, r * 0.18));
  oval(ctx, x, y, r * 0.55, r * 0.55, "#ffe08a");
  oval(ctx, x - r * 0.3, y - r * 0.35, r * 0.18, r * 0.12, "#fff7d6", null, 0, -0.6);
}

export function bowl(ctx, x, y, s, full = true) {
  if (full) oval(ctx, x, y - s * 0.42, s * 0.62, s * 0.3, "#c98e52", OUTLINE, s * 0.09);
  poly(ctx, [x - s * 0.85, y - s * 0.4, x + s * 0.85, y - s * 0.4, x + s * 0.6, y + s * 0.2,
    x - s * 0.6, y + s * 0.2], "#ef6f6c", OUTLINE, s * 0.1);
  line(ctx, [x - s * 0.5, y - s * 0.1, x + s * 0.5, y - s * 0.1], "#ffb3b0", s * 0.1);
}

export function acorn(ctx, x, y, s) {
  oval(ctx, x, y + s * 0.15, s * 0.5, s * 0.6, "#e0a25a", OUTLINE, s * 0.1);
  ctx.beginPath();
  ctx.ellipse(x, y - s * 0.15, s * 0.6, s * 0.42, 0, Math.PI, TAU);
  ctx.closePath();
  paint(ctx, "#8f6040", OUTLINE, s * 0.1);
  line(ctx, [x, y - s * 0.55, x + s * 0.12, y - s * 0.78], OUTLINE, s * 0.12);
}

export function envelope(ctx, x, y, s) {
  rrect(ctx, x - s, y - s * 0.65, s * 2, s * 1.3, s * 0.18, "#fffdf5", OUTLINE, s * 0.14);
  line(ctx, [x - s * 0.9, y - s * 0.5, x, y + s * 0.12, x + s * 0.9, y - s * 0.5], OUTLINE, s * 0.12);
  heart(ctx, x, y + s * 0.02, s * 0.2, "#ff6b8f");
}

export function parcel(ctx, x, y, s, label, bad = false) {
  rrect(ctx, x - s, y - s * 0.8, s * 2, s * 1.6, s * 0.2, bad ? "#f08a8a" : "#e8b877", OUTLINE,
    s * 0.14);
  line(ctx, [x, y - s * 0.8, x, y + s * 0.8], bad ? "#b83a3a" : "#b8793a", s * 0.22);
  text(ctx, label, x, y + s * 0.1, { size: s * 0.95, color: "#fff", stroke: OUTLINE, weight: 800 });
}

export function cone(ctx, x, y, s) {
  rrect(ctx, x - s * 0.6, y - s * 0.16, s * 1.2, s * 0.22, s * 0.08, "#f2793a", OUTLINE, s * 0.1);
  poly(ctx, [x - s * 0.38, y - s * 0.14, x + s * 0.38, y - s * 0.14, x + s * 0.1, y - s * 1.1,
    x - s * 0.1, y - s * 1.1], "#f2793a", OUTLINE, s * 0.1);
  line(ctx, [x - s * 0.22, y - s * 0.55, x + s * 0.22, y - s * 0.55], "#fff", s * 0.16);
}

export function zzz(ctx, x, y, time, s) {
  for (let i = 0; i < 3; i += 1) {
    const phase = (time * 0.5 + i / 3) % 1;
    ctx.globalAlpha = Math.sin(phase * Math.PI);
    text(ctx, "z", x + phase * s * 0.9 + Math.sin(phase * 6) * 2, y - phase * s * 1.5,
      { size: s * (0.5 + phase * 0.5), color: "#6d7fb8", stroke: "#fff", weight: 800 });
  }
  ctx.globalAlpha = 1;
}

export function anger(ctx, x, y, r) {
  ctx.strokeStyle = "#e5484d";
  ctx.lineWidth = r * 0.34;
  ctx.lineCap = "round";
  for (const [sx, sy] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) {
    ctx.beginPath();
    ctx.arc(x + sx * r, y + sy * r, r * 0.72, Math.atan2(-sy, -sx) - 0.75, Math.atan2(-sy, -sx) + 0.75);
    ctx.stroke();
  }
}

export function text(ctx, value, x, y, options = {}) {
  const { size = 14, color = OUTLINE, stroke = null, weight = 700, align = "center",
    strokeWidth = size * 0.28 } = options;
  ctx.font = `${weight} ${size}px ${FONT}`;
  ctx.textAlign = align;
  ctx.textBaseline = "middle";
  if (stroke) {
    ctx.lineJoin = "round";
    ctx.strokeStyle = stroke;
    ctx.lineWidth = strokeWidth;
    ctx.strokeText(value, x, y);
  }
  ctx.fillStyle = color;
  ctx.fillText(value, x, y);
}

export function measure(ctx, value, size, weight = 700) {
  ctx.font = `${weight} ${size}px ${FONT}`;
  return ctx.measureText(value).width;
}

/** A small rounded speech bubble with its tail pointing down at (x, y). */
export function bubble(ctx, value, x, y, options = {}) {
  const { size = 14, color = OUTLINE, fill = "#fff" } = options;
  const width = measure(ctx, value, size) + size * 1.3;
  const height = size * 1.75;
  const top = y - height - size * 0.55;
  poly(ctx, [x - size * 0.4, top + height - 1, x + size * 0.4, top + height - 1, x, y], fill,
    OUTLINE, 2);
  rrect(ctx, x - width / 2, top, width, height, height / 2, fill, OUTLINE, 2);
  rrect(ctx, x - size * 0.34, top + height - 4, size * 0.68, 4, 0, fill);
  text(ctx, value, x, top + height / 2 + 1, { size, color });
}
