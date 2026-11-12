/**
 * Motion kit: everything is a pure function of time, so any frame can be rendered on its own.
 * No CSS animations, no timers. A scene builds its DOM once, then `update(t)` styles it.
 */
import { drawCritter, zzz } from "/zoo/static/js/art.js";

export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, k) => a + (b - a) * k;

export const E = {
  lin: (x) => x,
  in: (x) => x * x * x,
  out: (x) => 1 - (1 - x) ** 3,
  outExpo: (x) => (x >= 1 ? 1 : 1 - 2 ** (-10 * x)),
  inOut: (x) => (x < 0.5 ? 4 * x * x * x : 1 - (-2 * x + 2) ** 3 / 2),
  outBack: (x) => 1 + 2.4 * (x - 1) ** 3 + 1.4 * (x - 1) ** 2,
};

/** Progress 0..1 of a tween starting at t0 lasting d seconds. */
export const p = (t, t0, d, ease = E.out) => ease(clamp((t - t0) / d));

/** The house "pop": a damped spring 0 -> 1 with about 11% overshoot. */
export function spring(t, t0, damp = 9, freq = 13) {
  const x = t - t0;
  return x <= 0 ? 0 : 1 - Math.exp(-damp * x) * Math.cos(freq * x);
}

/** Deterministic pseudo random in 0..1 from an integer seed. */
export function rnd(seed) {
  const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
}

export function h(tag, cls, parent, html) {
  const el = document.createElement(tag);
  if (cls) el.className = cls;
  if (html !== undefined) el.innerHTML = html;
  if (parent) parent.appendChild(el);
  return el;
}

/**
 * Place an element. (x, y) is where its anchor lands on the 1920x1080 stage.
 * anchor: "c" center (default), "l" left-middle, "tl" top-left.
 */
export function put(el, { x = 0, y = 0, s = 1, sx = s, sy = s, r = 0, o = 1, blur = 0, anchor = "c" } = {}) {
  const shift = anchor === "c" ? "translate(-50%,-50%)" : anchor === "l" ? "translate(0,-50%)" : "";
  el.style.transformOrigin = anchor === "c" ? "50% 50%" : anchor === "l" ? "0 50%" : "0 0";
  el.style.transform = `translate(${x}px,${y}px) ${shift} rotate(${r}deg) scale(${sx},${sy})`;
  el.style.opacity = clamp(o);
  el.style.visibility = o <= 0.001 ? "hidden" : "visible";
  el.style.filter = blur > 0.05 ? `blur(${blur}px)` : "";
}

/** Pop in at `a` with the spring, leave at `b` by shrinking and fading. Returns {s, o}. */
export function pop(t, a, b = Infinity) {
  const leave = p(t, b, 0.22, E.in);
  return { s: spring(t, a) * (1 - leave * 0.25), o: p(t, a, 0.1) * (1 - leave) };
}

/** An animal from the game, drawn by the game's own art module. face=true is a head shot. */
export function critter(parent, kind, size, { face = false } = {}) {
  const c = h("canvas", "", parent);
  const S = size * 2;
  c.width = S;
  c.height = S;
  c.style.width = `${size}px`;
  c.style.height = `${size}px`;
  const ctx = c.getContext("2d");
  c.draw = (o = {}) => {
    ctx.clearRect(0, 0, S, S);
    if (face) drawCritter(ctx, kind, S / 2, S * 1.28, S * 1.42, { shadow: false, ...o });
    else drawCritter(ctx, kind, S / 2, S * 0.92, S * 0.72, o);
    if (o.sleep) zzz(ctx, S * 0.66, S * (face ? 0.3 : 0.24), o.time || 0, S * 0.11);
  };
  c.draw();
  return c;
}

/** Natural eyes: open, with a short blink every few seconds, offset per character. */
export const blink = (t, offset = 0) => ((t + offset) % 3.1 < 0.13 ? "blink" : "open");

export function cursor(parent, kind, name, color) {
  const el = h("div", "cursor abs", parent);
  el.style.setProperty("--chip", color);
  el.innerHTML = `<svg viewBox="0 0 44 44"><path d="M5 4 L36 17 L22 22 L17 37 Z" fill="${color}" stroke="#4b3757" stroke-width="4" stroke-linejoin="round"/></svg>`;
  const tag = h("div", "tag", el);
  el.face = critter(tag, kind, 34, { face: true });
  h("span", "", tag, name);
  return el;
}

/** Typing schedule: when (0..1) each character of `text` appears. Humanized but deterministic. */
export function typing(text, seed = 1) {
  const at = [];
  let clock = 0;
  let lineStart = true;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (ch === "\n") { clock += 3.5; lineStart = true; }
    else if (ch === " " && lineStart) clock += 0.02; // auto indent
    else { clock += 0.55 + rnd(seed + i) * 0.9 + (",.:)".includes(text[i - 1]) ? 0.8 : 0); lineStart = false; }
    at.push(clock);
  }
  return at.map((v) => v / clock);
}
export const typedCount = (schedule, k) => {
  let n = 0;
  while (n < schedule.length && schedule[n] <= k) n += 1;
  return n;
};

/** Width in px of a string in a given CSS font, for carets and left anchored typing. */
const measurer = document.createElement("canvas").getContext("2d");
export function textWidth(text, font) {
  measurer.font = font;
  return measurer.measureText(text).width;
}

/** Captured gameplay (see capture-game.mjs) shown inside a rounded window. */
export async function loadClip(name) {
  const base = `../assets/game/${name}/`;
  const meta = await (await fetch(`${base}index.json`)).json();
  return { base, ...meta };
}
export function clipWindow(parent, clip, width) {
  const el = h("div", "window abs", parent);
  const k = width / clip.box.width;
  const height = clip.box.height * k;
  el.style.width = `${width}px`;
  el.style.height = `${height}px`;
  const img = h("img", "", el);
  img.style.width = `${clip.page[0] * k}px`;
  img.style.left = `${-clip.box.x * k - 6}px`;
  img.style.top = `${-clip.box.y * k - 6}px`;
  el.size = [width, height];
  let current = "";
  /** Show the frame for clip time `tc`; resolves when the image is decoded. */
  el.show = (tc) => {
    const frames = clip.frames;
    let lo = 0;
    let hi = frames.length - 1;
    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1;
      if (frames[mid].t <= tc) lo = mid; else hi = mid - 1;
    }
    const file = frames[lo].file;
    if (file === current) return null;
    current = file;
    img.src = clip.base + file;
    return img.decode().catch(() => {});
  };
  return el;
}
