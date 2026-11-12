/**
 * Zoo Ops, film 2: same story, told with the reference's grammar (MOTION_PLAYBOOK.md, part 2).
 * 57.75 s at 24 fps like the reference. Timings marked "measured" come from tools/analyze_reference.py.
 */
import { E, blink, clamp, clipWindow, critter, h, lerp, loadClip, p, put, rnd, spring, typedCount, typing } from "./kit.js";
import { ICONS } from "./icons.js";

export const DURATION = 57.75;
export const FPS = 24;
const F = 1 / 24;

const PATTERNS = [
  ["Cache", "database-zap", "#c2622a"], ["Rate limit", "gauge", "#2a5fb8"], ["Reliability", "shield-check", "#1e7a3a"],
  ["Idempotency", "repeat", "#5b3cc4"], ["Observability", "eye", "#0f7f78"], ["DB speed", "zap", "#b07a12"],
  ["Integrity", "lock", "#a3123a"], ["Async", "list-ordered", "#8b1a6b"], ["Auth", "key-round", "#3f5fae"],
  ["Deploy", "rocket", "#4f7d12"],
];
const HAZEL = "#c2622a";
const GUS = "#17806d";
const BEA = "#b5389a";
const YOU = "#2f5fcb";

const stage = document.getElementById("stage");
const scenes = [];
function scene(a, b, build, tin = "up", tout = "up") {
  const root = h("div", "scene", stage);
  scenes.push({ a, b, root, tin, tout, update: build(root) });
}
const soft = (t, a) => spring(t, a, 11, 12); // 5 % overshoot: tags, icons, bubbles
const show = (t, a, b = Infinity) => p(t, a, 0.12) * (1 - p(t, b, 0.12));

function icon(parent, name, color, size) {
  const el = h("div", "icon", parent, `<svg viewBox="0 0 24 24" width="${size}" height="${size}">${ICONS[name]}</svg>`);
  el.style.color = color;
  const parts = [...el.querySelectorAll("svg > *")];
  for (const part of parts) { part.setAttribute("pathLength", "1"); part.setAttribute("stroke-dasharray", "1"); }
  /** Draw the strokes on, 0..1, like a pen. */
  el.draw = (k) => {
    for (const part of parts) part.setAttribute("stroke-dashoffset", 1 - clamp(k));
    el.firstChild.style.opacity = k > 0.01 ? 1 : 0;
  };
  return el;
}
function cur(parent, name, color) {
  const el = h("div", "cur", parent, `<svg viewBox="0 0 22 22"><path d="M2 2 L19 8.5 L11 11.5 L8 19.5 Z" fill="${color}" stroke="#fff" stroke-width="1.5" stroke-linejoin="round"/></svg>${name ? `<span class="tag">${name}</span>` : ""}`);
  el.style.setProperty("--c", color);
  el.tag = el.querySelector(".tag");
  return el;
}
/** A cursor gliding on a soft arc from a to b. */
function glide(el, t, t0, d, a, b, o = 1) {
  const k = p(t, t0, d, E.inOut);
  put(el, { x: lerp(a[0], b[0], k) + Math.sin(k * Math.PI) * 30, y: lerp(a[1], b[1], k) - Math.sin(k * Math.PI) * 18, anchor: "tl", o });
}

/* --------------------------------------------------------------- 0. Canvas grid --------- */
function sGrid(root) {
  const lines = [];
  for (let x = 60; x < 1920; x += 60) lines.push([x, 0, 1, 1080, "0 0"]);
  for (let y = 60; y < 1080; y += 60) lines.push([0, y, 1920, 1, "0 0"]);
  const els = lines.map(([x, y, w, hh], i) => {
    const el = h("div", "gridline", root);
    el.style.cssText = `left:${x}px;top:${y}px;width:${w}px;height:${hh}px;transform-origin:${rnd(i) > 0.5 ? "0 0" : "100% 100%"}`;
    return el;
  });
  return (t) => {
    const out = 1 - p(t, 25.2, 0.5);
    els.forEach((el, i) => {
      const k = p(t, 6.5 + rnd(i + 9) * 1.3, 0.5, E.out);
      el.style.transform = i < 31 ? `scaleY(${k})` : `scaleX(${k})`;
      el.style.opacity = k * out;
    });
  };
}

/* ---------------------------------------------------------------- 1. Cold open ---------- */
function sTitle(root) {
  const text = "System design";
  const wrap = h("div", "serif t-title", root);
  const chars = [...text].map((ch) => h("span", "", wrap, ch === " " ? "&nbsp;" : ch));
  const W = wrap.offsetWidth;
  const x0 = 960 - W / 2;
  const right = chars.map((c) => c.offsetLeft + c.offsetWidth);
  const chip = h("div", "chip", root, "Learn");
  const caret = h("div", "caret2", root);
  caret.style.cssText = `height:150px;--c:${HAZEL}`;
  const name = h("div", "lab", root, "Hazel");
  name.style.setProperty("--c", HAZEL);
  const pointer = cur(root, "Hazel", HAZEL);
  const icons = PATTERNS.map(([, ic, color]) => icon(root, ic, color, 62));
  const T0 = 17 * F; // measured: first letter at frame 17, then one letter every 2 frames
  const at = chars.map((_, i) => T0 + i * 2 * F + (i === chars.length - 1 ? 2 * F : 0));
  const END = at[at.length - 1];
  const MORPH = 2.6;

  return (t) => {
    put(wrap, { x: x0, y: 540, anchor: "l" });
    let n = 0;
    chars.forEach((c, i) => {
      const gone = t >= MORPH + i * 0.115;
      if (t >= at[i]) n = i + 1;
      c.style.opacity = t >= at[i] && !gone ? 1 : 0;
      c.style.color = t - at[i] < 2.5 * F ? HAZEL : ""; // the newest letter is tinted for a beat
    });
    const c1 = soft(t, 0.25);
    put(chip, { x: x0 + 6, y: 418, anchor: "l", s: c1, o: show(t, 0.25, MORPH + 0.1) });

    const cx = x0 + (n ? right[n - 1] : 0) + 6;
    const typingNow = t < END + 0.25;
    put(caret, { x: cx, y: 540, sy: soft(t, 0.42), o: t > 0.42 && typingNow ? 1 : 0 });
    put(name, { x: cx + 2, y: 452, anchor: "l", s: soft(t, 0.5), o: t > 0.5 && typingNow ? 1 : 0 });
    // Typing done: the caret becomes an ordinary cursor and wanders off.
    const k = p(t, END + 0.25, 1.0, E.inOut);
    put(pointer, { x: lerp(cx, x0 + W * 0.42, k), y: lerp(600, 668, k), anchor: "tl", s: lerp(0.6, 1, p(t, END + 0.25, 0.2)),
      o: typingNow ? 0 : 1 - p(t, 4.5, 0.3) });

    icons.forEach((el, i) => {
      const a = MORPH + 0.06 + i * 0.15;
      const out = p(t, 4.55 + (icons.length - 1 - i) * 0.055, 0.14, E.in);
      el.draw(p(t, a, 0.34, E.out));
      put(el, { x: x0 + 36 + i * 80, y: 540, s: lerp(0.55, 1, soft(t, a)) * (1 - out * 0.5), o: 1 - out });
    });
  };
}

/* ------------------------------------------------ 2. Chapter card: dragged into place ---- */
function chapterCard(root, iconName, color, a, b) {
  const ic = icon(root, iconName, color, 46);
  const l1 = h("div", "serif t-card", root, a);
  const l2 = h("div", "serif t-card", root, b);
  l1.style.fontWeight = 400;
  l2.style.fontWeight = 700;
  return { ic, l1, l2 };
}
function sChapter1(root) {
  const { ic, l1, l2 } = chapterCard(root, "gamepad-2", BEA, "Break it in", "a tiny zoo");
  const mk = (line, color, name) => {
    const box = h("div", "selbox", root);
    box.style.setProperty("--c", color);
    const lab = h("div", "lab", root, name);
    lab.style.setProperty("--c", color);
    return { line, box, lab, w: line.offsetWidth + 14, hh: line.offsetHeight + 4 };
  };
  const A = mk(l1, HAZEL, "Hazel");
  const B = mk(l2, BEA, "Bea");
  const cursors = [cur(root, "Hazel", HAZEL), cur(root, "Bea", BEA), cur(root, "Gus", GUS)];
  const card = h("div", "prompt card", root, `<small>Terminal</small><div class="in"></div>
    <div class="row"><span class="box">✓</span> Open the gates <span class="go"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">${ICONS["arrow-up"]}</svg></span></div>`);
  const input = card.querySelector(".in");
  const avatar = h("div", "avatar", root, "YOU");
  const you = cur(root, "", "#1a1a18");
  const say = "so cozy";

  const fly = (item, t, t0, from, to, r0, slide) => {
    const k = p(t, t0, 1.25, E.out);
    const x = lerp(lerp(from[0], to[0], k), to[0] - 640, slide);
    const y = lerp(lerp(from[1], to[1], k) - Math.sin(k * Math.PI) * 60, to[1] + 290, slide);
    const s = lerp(1, 1.45, slide);
    const r = lerp(r0, 0, k);
    const o = t >= t0 ? 1 : 0;
    put(item.line, { x, y, r, s, o });
    const held = o * (1 - p(t, t0 + 1.4, 0.08));
    item.box.style.width = `${item.w}px`;
    item.box.style.height = `${item.hh}px`;
    put(item.box, { x, y: y - 2, r, o: held });
    const rad = (r * Math.PI) / 180;
    put(item.lab, { x: x - Math.sin(rad) * (item.hh / 2 + 4), y: y + Math.cos(rad) * (item.hh / 2 + 4), r, o: held });
  };

  return (t) => {
    const slide = p(t, 8.0, 0.8, E.inOut);
    fly(A, t, 4.9, [250, 190], [960, 520], 20, slide);
    fly(B, t, 5.55, [2180, 640], [960, 596], -11, slide);
    ic.draw(p(t, 6.1, 0.4, E.out));
    put(ic, { x: lerp(960, 320, slide), y: lerp(448, 705, slide), s: lerp(0.6, 1, soft(t, 6.1)) * lerp(1, 1.45, slide) });

    // Three keepers hang around the title; one leaves a comment.
    const co = 1 - p(t, 10.1, 0.2);
    glide(cursors[0], t, 6.35, 0.9, [960, 548], [lerp(690, 250, slide), lerp(600, 990, slide)], show(t, 6.35) * co);
    glide(cursors[1], t, 6.95, 0.9, [960, 620], [lerp(905, 420, slide), lerp(660, 1010, slide)], show(t, 6.95) * co);
    glide(cursors[2], t, 6.6, 1.0, [1700, 380], [lerp(1180, 1560, slide), lerp(650, 560, slide)], show(t, 6.6) * co);
    const typed = say.slice(0, Math.round(p(t, 7.35, 0.6, E.lin) * say.length));
    cursors[2].tag.textContent = typed || "Gus";
    cursors[2].tag.style.borderRadius = typed ? "14px" : "6px";

    // The prompt card: type the command, tick, send.
    const c = soft(t, 8.35);
    put(card, { x: 1120, y: 800, s: lerp(0.92, 1, c), o: show(t, 8.35) });
    put(avatar, { x: 800, y: 735, s: c, o: show(t, 8.3) });
    const cmd = " play";
    const n = Math.round(p(t, 8.95, 0.5, E.lin) * cmd.length);
    const caretOn = t < 9.9 && Math.floor(t * 2.6) % 2 === 0;
    input.innerHTML = `<span class="at">python -m zoo</span>${cmd.slice(0, n)}<span style="opacity:${caretOn ? 1 : 0}">|</span>`;
    glide(you, t, 9.3, 0.6, [1500, 1000], [1362, 872], show(t, 9.3));
    const press = 1 - Math.sin(Math.PI * clamp((t - 10.0) / 0.2)) * 0.12;
    card.querySelector(".go").style.transform = `scale(${press})`;
  };
}

/* ------------------------------------------------------ 3. Demo: the zoo is on fire ------ */
function annotate(root, color, name, label) {
  const box = h("div", "selbox", root);
  box.style.cssText = `--c:${color};border-radius:6px`;
  const lab = h("div", "lab", root, label);
  lab.style.setProperty("--c", color);
  return { box, lab, cur: cur(root, name, color) };
}
function drawNote(note, t, at, out, rect, from) {
  const [x, y, w, hh] = rect;
  const k = p(t, at, 0.4, E.out);
  const o = show(t, at, out);
  note.box.style.width = `${w * k}px`;
  note.box.style.height = `${hh * k}px`;
  put(note.box, { x, y, anchor: "tl", o });
  put(note.lab, { x, y: y - 31, anchor: "tl", s: soft(t, at + 0.3), o: show(t, at + 0.3, out) });
  const arrive = p(t, at - 0.75, 0.75, E.inOut);
  put(note.cur, { x: lerp(from[0], x, arrive) + w * k, y: lerp(from[1], y, arrive) + hh * k, anchor: "tl", o: show(t, at - 0.75, out) });
}
function sDemo1(root, clip) {
  const win = clipWindow(root, clip, 1500);
  const [W, H] = win.size;
  const n1 = annotate(root, HAZEL, "Hazel", "Hazel · asleep");
  const n2 = annotate(root, GUS, "Gus", "30 Owl calls for 6 questions");
  const n3 = annotate(root, BEA, "Bea", "coins draining");
  const FOCUS = [0.365, 0.5];
  return (t, pending) => {
    const zoom = p(t, 18.0, 1.3, E.inOut);
    const s = lerp(lerp(1, 1.04, p(t, 10.4, 8, E.lin)), 1.75, zoom);
    const cx = lerp(960, 960 - (FOCUS[0] - 0.5) * W * 1.75, zoom);
    const cy = lerp(560, 540 - (FOCUS[1] - 0.5) * H * 1.75, zoom) + Math.sin(t * 0.5) * 4;
    put(win, { x: cx, y: cy, s });
    pending.push(win.show(1.6 + (t - 10.4)));
    const at = (fx, fy, w, hh) => [cx + (fx - 0.5) * W * s - (w * s) / 2, cy + (fy - 0.5) * H * s - (hh * s) / 2, w * s, hh * s];
    drawNote(n1, t, 12.4, 22, at(0.365, 0.5, 150, 140), [300, 1000]);
    drawNote(n2, t, 14.2, 17.7, at(0.5, 0.31, 170, 190), [1750, 250]);
    drawNote(n3, t, 16.0, 17.7, at(0.055, 0.047, 120, 54), [200, 420]);
  };
}

/* ------------------------------------------------------ 4. Chapter 2 and the code -------- */
const HEAD = "def get_or_load(self, key, loader, ttl=None):";
const TODO = "    # TODO(level 01): cache-aside read path";
const BODY = [
  "    k = self.redis_key(key)",
  "    cached = self._redis.get(k)",
  "    if cached is not None:",
  "        return json.loads(cached)        # hit",
  "",
  "    value = loader()                     # miss",
  "    self._redis.set(k, json.dumps(value),",
  "                    ex=ttl or self._default_ttl)",
  "    return value",
].join("\n");
const TOKEN = /(#.*$)|\b(def|if|is|not|return|or)\b|\b(None)\b|\b(self)\b|([A-Za-z_]\w*)(?=\()|(\w+|[^\w#]+)/g;
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
const paint = (line) => line.replace(TOKEN, (m, cm, kw, nb, self, fn) => {
  const cls = cm ? "cm" : kw ? "kw" : nb ? "nb" : self ? "self" : fn ? "fn" : "";
  return cls ? `<span class="${cls}">${esc(m)}</span>` : esc(m);
});
const ASK = "Level 01: cache what the Owl has already answered.";

function sChapter2(root) {
  const { ic, l1, l2 } = chapterCard(root, "code-xml", "#1e7a3a", "Fix it with", "a few lines of Python");
  const bubble = h("div", "bubble", root, ASK);
  bubble.style.width = "520px";
  const reply = h("div", "serif", root);
  reply.style.cssText = "font-size:34px";
  return (t) => {
    const blur = p(t, 25.0, 0.45, E.inOut) * 9; // focus pull: the title goes soft, the bubble stays sharp
    ic.draw(p(t, 22.5, 0.4, E.out));
    put(ic, { x: 960, y: 170, blur });
    put(l1, { x: 960, y: 246, blur });
    put(l2, { x: 960, y: 322, blur });
    const b = soft(t, 23.3);
    put(bubble, { x: 990, y: 420, anchor: "tl", s: lerp(0.85, 1, b), o: show(t, 23.3) });
    reply.textContent = "On it.".slice(0, Math.round(p(t, 24.5, 0.3, E.lin) * 6));
    put(reply, { x: 600, y: 640, anchor: "l" });
  };
}

function sDemo2(root, clip) {
  const app = h("div", "app card", root, `<div class="top"><b></b><b></b><b></b>zoo-ops</div>
    <div class="chat"><div class="bubble">${ASK}</div><p>On it.</p><div class="st"></div></div>
    <div class="ed"><div class="tab">levels/l01_cache/cache.py</div><div class="code2"></div><div class="tests"></div></div>`);
  const code = app.querySelector(".code2");
  code.style.setProperty("--c", YOU);
  const status = app.querySelector(".st");
  const tests = app.querySelector(".tests");
  const TESTS = ["llm key changes with model or prompt", "sampled calls are not cached",
    "embed many only pays for missing texts", "embed many skips the provider when all cached"];
  const sched = typing(BODY, 3);
  const win = clipWindow(root, clip, 880);
  const [W, H] = win.size;
  const note = annotate(root, HAZEL, "Hazel", "Hazel · awake");
  const stat = h("div", "stat card", root, '<div class="n"><s>30</s><i>→</i><span></span></div><small>Owl calls, for the same 30 visitors</small>');
  const six = stat.querySelector("span");

  return (t, pending) => {
    const side = p(t, 33.2, 0.9, E.inOut);
    put(app, { x: lerp(960, 500, side), y: lerp(575, 560, side), s: lerp(1, 0.8, side) });

    let html = `<span class="ln">${paint(HEAD)}</span>`;
    if (t < 26.35) {
      html += `<span class="ln"><span class="${t > 25.95 ? "todo" : ""}">${esc(TODO)}</span></span>`;
    } else {
      const n = typedCount(sched, p(t, 26.5, 4.8, E.lin));
      const lines = BODY.slice(0, n).split("\n");
      lines.forEach((line, i) => {
        const last = i === lines.length - 1 && t < 31.45;
        html += `<span class="ln${last ? " act" : ""}">${paint(line)}${last ? '<span class="who">You</span>' : ""}</span>`;
      });
    }
    if (code.innerHTML !== html) code.innerHTML = html;

    const dots = ".".repeat(1 + (Math.floor(t * 3) % 3));
    const done = TESTS.filter((_, i) => t >= 31.75 + i * 0.3).length;
    status.textContent = t < 31.45 ? `Writing get_or_load${dots}` : done < 4 ? `Running the tests${dots}` : "4 of 4 green. Hazel is awake.";
    tests.style.transform = `translateY(${lerp(222, 0, p(t, 31.45, 0.4, E.outExpo))}px)`;
    const rows = TESTS.slice(0, done).map((name) => `<div><span class="ok">PASS</span>${name}</div>`).join("");
    const thtml = `<div class="hd">$ python -m zoo test 1</div>${rows}`;
    if (tests.innerHTML !== thtml) tests.innerHTML = thtml;

    // Payoff: the same zoo with the cache built.
    const wx = lerp(2500, 1425, p(t, 33.3, 0.9, E.outExpo));
    put(win, { x: wx, y: 470 });
    if (t > 33.2) pending.push(win.show(3 + (t - 33.2)));
    drawNote(note, t, 34.6, 99, [wx + (0.365 - 0.5) * W - 62, 470 - 50, 124, 104], [1700, 900]);
    const st = soft(t, 35.2);
    six.textContent = Math.round(lerp(30, 6, p(t, 35.3, 0.7, E.out)));
    six.style.color = "#1e7a3a";
    put(stat, { x: 1425, y: 885, s: lerp(0.9, 1, st), o: show(t, 35.2) });
  };
}

/* ------------------------------------------------------- 5. Chapter 3 and the diagram ---- */
function sChapter3(root) {
  const { ic, l1, l2 } = chapterCard(root, "layers", YOU, "See why", "under the hood");
  return (t) => {
    ic.draw(p(t, 37.7, 0.4, E.out));
    put(ic, { x: 960, y: 448 });
    put(l1, { x: 960, y: 520 });
    put(l2, { x: 960, y: 596 });
  };
}

function sArch(root) {
  const cam = h("div", "cam", root);
  const QUESTIONS = [0, 1, 0, 2, 3, 1, 0, 4, 2, 3, 1, 5, 0, 2, 4, 1, 3, 5, 0, 2, 1, 4, 3, 5, 0, 1, 2, 3, 4, 5];
  const COLORS = PATTERNS.slice(0, 6).map((x) => x[2]);
  const T1 = 39.9;
  const SWITCH = 42.1;
  const T2 = 43.0;
  const BTN = [1690, 150];

  const wires = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  wires.setAttribute("class", "wires");
  cam.appendChild(wires);
  const wire = () => wires.appendChild(document.createElementNS("http://www.w3.org/2000/svg", "line"));
  const wVA = wire();
  const wAS = wire();
  const wAR = wire();
  const node = (inner, label, sub) => ({ el: h("div", "node card", cam, inner), text: h("div", "nlabel", cam, `${label}<small>${sub}</small>`) });
  const nV = node("", "Visitors", "30 questions");
  const visitor = critter(nV.el, "rabbit", 110, { face: true });
  const nA = node('<img src="../assets/logos/fastapi.svg">', "API", "FastAPI");
  const nS = node('<img src="../assets/logos/postgresql.svg">', "Source of truth", "LLM · database · slow");
  const nR = node('<img src="../assets/logos/redis.svg">', "Redis", "cache · TTL");
  const slots = COLORS.map(() => h("div", "slot2", cam));
  const hitTag = h("div", "lab", cam, "hit: instant");
  hitTag.style.setProperty("--c", "#1e7a3a");
  const missTag = h("div", "lab", cam, "miss: load once, set + TTL");
  missTag.style.setProperty("--c", "#6f6c64");
  const titleA = h("div", "serif", cam, "Without a cache");
  const titleB = h("div", "serif", cam, "With Redis");
  titleA.style.cssText = titleB.style.cssText = "font-size:64px;font-weight:500";
  const big = h("div", "big2", cam);
  const cap = h("div", "", cam, "Owl calls");
  cap.style.cssText = "font:500 30px Inter";
  const hits = h("div", "chip", cam);
  const btn = h("div", "btn", cam, `Next pattern <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>`);
  const arrow = h("div", "", cam, '<svg viewBox="0 0 22 22" width="30" height="30" style="overflow:visible"><path d="M2 2 L19 8.5 L11 11.5 L8 19.5 Z" fill="#1a1a18" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>');

  const first = new Set();
  const legs1 = [["V", "A", 0.18], ["A", "S", 0.35], ["S", "S", 0.2], ["S", "A", 0.3], ["A", "V", 0.18]];
  const legsHit = [["V", "A", 0.18], ["A", "R", 0.12], ["R", "R", 0.06], ["R", "A", 0.12], ["A", "V", 0.18]];
  const legsMiss = [["V", "A", 0.18], ["A", "R", 0.12], ["R", "A", 0.12], ["A", "S", 0.35], ["S", "S", 0.2],
    ["S", "A", 0.3], ["A", "R", 0.12], ["R", "A", 0.12], ["A", "V", 0.18]];
  const requests = [];
  QUESTIONS.forEach((q, i) => requests.push({ q, start: T1 + i * 0.045, legs: legs1, call: 0.53, phase: 1 }));
  QUESTIONS.forEach((q, i) => {
    const miss = !first.has(q);
    first.add(q);
    requests.push({ q, start: T2 + i * 0.055, legs: miss ? legsMiss : legsHit, phase: 2,
      call: miss ? 0.77 : null, hit: miss ? null : 0.3, stored: miss ? 1.39 : null });
  });
  for (const r of requests) {
    r.el = h("div", "dot2", cam);
    r.el.style.background = COLORS[r.q];
    r.total = r.legs.reduce((sum, leg) => sum + leg[2], 0);
  }

  return (t) => {
    // Camera: at the end, push in on one small button, like a macro lens.
    const z = p(t, 45.55, 0.85, E.inOut);
    cam.style.transformOrigin = `${BTN[0]}px ${BTN[1]}px`;
    cam.style.transform = `translate(${lerp(0, 960 - BTN[0], z)}px,${lerp(0, 540 - BTN[1], z)}px) scale(${lerp(1, 3.4, z)})`;

    const two = p(t, SWITCH, 0.7, E.inOut);
    const P = { V: [780, 560], A: [1080, 560], S: [1520, lerp(560, 790, two)], R: [1520, lerp(560, 330, two)] };
    const line = (el, a, b, o) => {
      el.setAttribute("x1", P[a][0] + 82); el.setAttribute("y1", P[a][1] + (P[b][1] - P[a][1]) * 0.2);
      el.setAttribute("x2", P[b][0] - 82); el.setAttribute("y2", P[b][1] - (P[b][1] - P[a][1]) * 0.2);
      el.style.opacity = o;
    };
    line(wVA, "V", "A", p(t, 39.6, 0.3));
    line(wAS, "A", "S", p(t, 39.7, 0.3));
    line(wAR, "A", "R", two);
    const place = (n, key, at, o = 1) => {
      put(n.el, { x: P[key][0], y: P[key][1], s: lerp(0.8, 1, soft(t, at)), o: show(t, at) * o });
      put(n.text, { x: P[key][0], y: P[key][1] + 120, o: p(t, at + 0.1, 0.25) * o });
    };
    place(nV, "V", 39.35);
    place(nA, "A", 39.45);
    place(nS, "S", 39.55);
    place(nR, "R", SWITCH + 0.1, two);
    visitor.draw({ eyes: t < SWITCH ? "sad" : t > T2 + 0.5 ? "happy" : blink(t) });

    let calls = 0;
    let hitCount = 0;
    const stored = new Set();
    const phase = t < SWITCH + 0.5 ? 1 : 2;
    for (const r of requests) {
      const dt = t - r.start;
      if (r.phase === phase && r.call !== null && dt >= r.call) calls += 1;
      if (r.phase === 2 && r.hit && dt >= r.hit) hitCount += 1;
      if (r.phase === 2 && r.stored && dt >= r.stored) stored.add(r.q);
      if (dt < 0 || dt > r.total) { r.el.style.visibility = "hidden"; continue; }
      let left = dt;
      let leg = r.legs[0];
      for (leg of r.legs) { if (left <= leg[2]) break; left -= leg[2]; }
      const k = E.inOut(clamp(left / leg[2]));
      put(r.el, { x: lerp(P[leg[0]][0], P[leg[1]][0], k), y: lerp(P[leg[0]][1], P[leg[1]][1], k) + (r.q - 2.5) * 4 });
    }
    slots.forEach((slot, i) => {
      slot.style.background = stored.has(i) ? COLORS[i] : "transparent";
      slot.style.borderColor = stored.has(i) ? COLORS[i] : "";
      put(slot, { x: P.R[0] - 60 + i * 24, y: P.R[1] - 104, o: two });
    });
    put(hitTag, { x: 1300, y: 405, s: soft(t, T2 + 0.4), o: show(t, T2 + 0.4), r: -3 });
    put(missTag, { x: 1250, y: 730, s: soft(t, T2 + 0.9), o: show(t, T2 + 0.9), r: 2 });

    const sw = p(t, SWITCH, 0.35, E.inOut);
    put(titleA, { x: 150, y: 330, anchor: "l", o: p(t, 39.3, 0.3) * (1 - sw), blur: sw * 8 });
    put(titleB, { x: 150, y: 330, anchor: "l", o: sw, blur: (1 - sw) * 8 });
    big.textContent = calls;
    big.style.color = phase === 2 ? "#1e7a3a" : calls >= 30 ? "#b4232b" : "";
    put(big, { x: 142, y: 540, anchor: "l", o: p(t, 39.4, 0.25) });
    put(cap, { x: 150, y: 690, anchor: "l", o: p(t, 39.5, 0.3) });
    hits.textContent = `${hitCount} answered from the cache`;
    put(hits, { x: 150, y: 770, anchor: "l", s: soft(t, T2 + 0.35), o: show(t, T2 + 0.35) });

    const hover = t > 46.3;
    const press = 1 - Math.sin(Math.PI * clamp((t - 46.6) / 0.14)) * 0.05;
    btn.style.background = hover ? "#efede6" : "#fff";
    put(btn, { x: BTN[0], y: BTN[1], s: press, o: p(t, 39.6, 0.3) });
    const a = p(t, 45.8, 0.55, E.inOut);
    put(arrow, { x: lerp(1820, BTN[0] + 34, a), y: lerp(330, BTN[1] + 6, a), anchor: "tl", o: show(t, 45.8) });
  };
}

/* ----------------------------------------------------------- 6. The burst of tiles ------- */
function sCloud(root) {
  const logos = ["redis", "postgresql", "fastapi", "python"];
  const tiles = [];
  PATTERNS.forEach(([, ic, color]) => {
    const el = h("div", "tile", root);
    el.style.background = color;
    icon(el, ic, "#fff", 54).draw(1);
    tiles.push(el);
  });
  logos.forEach((name) => tiles.push(h("div", "tile w", root, `<img src="../assets/logos/${name}.svg">`)));
  const order = [0, 10, 3, 6, 11, 1, 8, 12, 4, 9, 13, 2, 7, 5];
  return (t) => {
    order.forEach((idx, i) => {
      const el = tiles[idx];
      const ang = (i / order.length) * Math.PI * 2 + rnd(i) * 0.5;
      const rad = 210 + rnd(i + 20) * 260;
      const out = E.outExpo(clamp((t - 46.75 - rnd(i + 5) * 0.12) / 0.8)) + Math.max(0, t - 46.75) * 0.05;
      const past = p(t, 48.55 + rnd(i + 7) * 0.25, 0.6, E.in); // then they fly past the camera
      const m = out * (1 + past * 4.5);
      put(el, { x: 960 + Math.cos(ang) * rad * 1.6 * m, y: 540 + Math.sin(ang) * rad * m,
        s: (0.55 + rnd(i + 3) * 0.75) * lerp(0.3, 1, clamp(out)) * (1 + past * 3.5),
        r: (rnd(i + 11) - 0.5) * 10, o: clamp(out * 4) * (1 - past), blur: past * 16 });
    });
  };
}

/* ------------------------------------------------------------------- 7. Tagline ---------- */
function sTagline(root) {
  const WORDS = [["Cache", 49.33], ["Retry", 50.0], ["Deploy", 50.58], ["Design", 51.17]]; // measured beat
  const line = h("div", "serif t-tag", root);
  const word = h("span", "", line);
  word.style.cssText = "padding:6px 10px 2px;margin:0 2px 0 -10px";
  h("span", "", line, " it like a zookeeper");
  const hazel = cur(root, "Hazel", HAZEL);
  const friends = [cur(root, "Gus", GUS), cur(root, "Bea", BEA), cur(root, "You", YOU)];
  const REACT = [["heart", "#e5484d", 820, 470, 52.2], ["sparkles", "#d99a00", 1310, 480, 52.38], ["heart", "#e5484d", 760, 500, 52.55],
    ["star", "#d99a00", 1380, 600, 52.7], ["heart", "#b5389a", 1235, 462, 52.85], ["sparkles", "#2f5fcb", 690, 600, 53.0]];
  const reacts = REACT.map(([name, color]) => {
    const el = icon(root, name, color, 40);
    el.draw(1);
    if (name !== "sparkles") el.firstChild.style.fill = color;
    return el;
  });
  return (t) => {
    let idx = 0;
    WORDS.forEach((w, i) => { if (t >= w[1]) idx = i; });
    word.textContent = WORDS[idx][0];
    const on = t >= 49.33 && t < 51.8;
    word.style.background = on ? "#a9c7d0" : "transparent";
    const out = p(t, 53.3, 0.2, E.in);
    put(line, { x: 960, y: 540, o: p(t, 49.15, 0.15) * (1 - out) });
    const wx = 960 - line.offsetWidth / 2 + word.offsetLeft + word.offsetWidth;
    const leave = p(t, 51.8, 0.7, E.inOut);
    put(hazel, { x: wx + leave * 90, y: 588 + leave * 70, anchor: "tl", o: show(t, 49.33) * (1 - out) });
    const spots = [[1420, 640], [600, 660], [1010, 650]];
    friends.forEach((el, i) => glide(el, t, 51.85 + i * 0.22, 0.7, [i % 2 ? -80 : 2000, 900 - i * 200], spots[i], show(t, 51.85 + i * 0.22) * (1 - out)));
    reacts.forEach((el, i) => {
      const [, , x, y, at] = REACT[i];
      const age = Math.max(0, t - at);
      put(el, { x, y: y - age * 34, s: soft(t, at), r: Math.sin(age * 5 + i) * 10, o: show(t, at) * (1 - out) });
    });
  };
}

/* ---------------------------------------------------------------------- 8. Logo ---------- */
function sLogo(root) {
  const mark = h("div", "", root);
  mark.style.cssText = "width:132px;height:132px;border-radius:50%;overflow:hidden;background:#f3e2c4";
  const owl = critter(mark, "owl", 132, { face: true });
  const name = h("div", "wordmark2", root, "Zoo Ops");
  const W = name.offsetWidth + 8;
  const cta = h("div", "", root, "python -m zoo play");
  cta.style.cssText = 'font:500 25px "JetBrains Mono";color:#6f6c64';
  const total = 132 + 26 + W;
  return (t) => {
    const k = p(t, 54.3, 0.7, E.inOut);
    const mx = lerp(960, 960 - total / 2 + 66, k);
    put(mark, { x: mx, y: 530, s: soft(t, 53.6), r: lerp(-90, 0, p(t, 53.6, 0.6, E.outExpo)), o: show(t, 53.6) });
    owl.draw({ eyes: t < 54.4 ? "happy" : blink(t) });
    name.style.width = `${W * k}px`;
    put(name, { x: mx + 66 + 26, y: 538, anchor: "l", o: k > 0 ? 1 : 0 });
    put(cta, { x: 960, y: 668, o: p(t, 55.3, 0.4) });
  };
}

/* ------------------------------------------------------------------- Timeline ---------- */
async function init() {
  for (const f of ['400 60px "Frank Ruhl Libre"', '500 60px "Frank Ruhl Libre"', '700 60px "Frank Ruhl Libre"',
    '400 20px "Inter"', '500 20px "Inter"', '600 20px "Inter"', '500 20px "JetBrains Mono"', '800 20px "Baloo 2"']) {
    await document.fonts.load(f);
  }
  const [before, after] = await Promise.all([loadClip("before"), loadClip("after")]);

  scene(0, DURATION, sGrid, "cut", "cut");
  scene(0, 5.3, sTitle, "cut", "cut");
  scene(4.7, 10.6, sChapter1, "cut", "up");
  scene(10.35, 22.4, (root) => sDemo1(root, before));
  scene(22.15, 25.75, sChapter2);
  scene(25.4, 37.7, (root) => sDemo2(root, after));
  scene(37.45, 39.45, sChapter3);
  scene(39.2, 46.75, sArch, "up", "cut");
  scene(46.75, 49.45, sCloud, "cut", "cut");
  scene(49.1, 53.6, sTagline, "cut", "cut");
  scene(53.45, 56.5, sLogo, "cut", "cut");
  scene(56.5, DURATION + 1, (root) => { h("div", "black", root); return () => {}; }, "cut", "cut"); // hard end on black

  window.seek = async (t) => {
    const pending = [];
    for (const sc of scenes) {
      const on = t >= sc.a && t < sc.b;
      sc.root.style.display = on ? "" : "none";
      if (!on) continue;
      // Scene changes are a whip: the old layer accelerates up and goes soft, the new one lands from below.
      const kin = sc.tin === "cut" ? 1 : p(t, sc.a, 0.55, E.outExpo);
      const kout = sc.tout === "cut" ? 0 : p(t, sc.b - 0.36, 0.36, E.in);
      sc.root.style.opacity = (sc.tin === "cut" ? 1 : p(t, sc.a, 0.14)) * (1 - p(t, sc.b - 0.1, 0.1) * (sc.tout === "cut" ? 0 : 1));
      sc.root.style.transform = `translateY(${(1 - kin) * 460 - kout * 760}px)`;
      sc.root.style.filter = kout > 0.02 ? `blur(${kout * 12}px)` : "";
      sc.update(t, pending);
    }
    await Promise.all(pending.filter(Boolean));
  };
  window.FILM = { duration: DURATION, fps: FPS };

  const params = new URLSearchParams(location.search);
  if (params.has("play") || params.has("t")) {
    const fit = () => { stage.style.transform = `scale(${Math.min(innerWidth / 1920, innerHeight / 1080)})`; };
    fit();
    addEventListener("resize", fit);
    let t = Number(params.get("t") || 0);
    let playing = params.has("play");
    let last = performance.now();
    addEventListener("keydown", (e) => {
      if (e.key === " ") playing = !playing;
      if (e.key === "ArrowRight") t += e.shiftKey ? 1 : F;
      if (e.key === "ArrowLeft") t -= e.shiftKey ? 1 : F;
    });
    const loop = async (now) => {
      if (playing) t += (now - last) / 1000;
      last = now;
      t = ((t % DURATION) + DURATION) % DURATION;
      await window.seek(t);
      document.getElementById("hud").textContent = `${t.toFixed(2)}s  frame ${Math.round(t * FPS)}`;
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }
  window.READY = true;
}
init();
