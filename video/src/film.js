/**
 * Zoo Ops: the 58 second presentation film.
 * Each scene is `scene(start, end, build)`; build() creates DOM once and returns update(t, pending).
 * Preview: open index.html?play through `npm run preview`. Render: `npm run render`.
 */
import { E, blink, clamp, clipWindow, critter, cursor, h, lerp, loadClip, p, pop, put, rnd, spring,
  textWidth, typedCount, typing } from "./kit.js";

export const DURATION = 58;
export const FPS = 30;

const PATTERNS = [
  ["Cache", "squirrel", "#d9822b"], ["Rate limit", "goose", "#2f8fd6"],
  ["Reliability", "fox", "#e2603a"], ["Idempotency", "cat", "#7a62d9"],
  ["Observability", "meerkat", "#159e8c"], ["DB speed", "mole", "#8a6a4a"],
  ["Integrity", "beaver", "#d9538a"], ["Async", "ant", "#b0483f"],
  ["Auth", "dog", "#3f5fae"], ["Deploy", "canary", "#6c9a1f"],
];
const tint = (color, pct = 24) => `color-mix(in srgb, ${color} ${pct}%, white)`;

const stage = document.getElementById("stage");
const scenes = [];
function scene(a, b, build) {
  const root = h("div", "scene", stage);
  scenes.push({ a, b, root, update: build(root) });
}

/* ------------------------------------------------------------------ 1. Title ---------- */
function sceneTitle(root) {
  const text = "System design";
  const font = '800 168px "Baloo 2"';
  const width = textWidth(text, font);
  const x0 = 960 - width / 2;
  const sched = typing(text, 7);

  const tagA = h("div", "pill", root, "a game about");
  const tagB = h("div", "pill", root, "10 patterns · 10 keepers");
  const title = h("div", "h-xl", root);
  const underline = h("div", "", root, `<svg width="${width}" height="40" style="overflow:visible"><path fill="none" stroke="#58c96c" stroke-width="12" stroke-linecap="round" pathLength="1" stroke-dasharray="1" /></svg>`);
  const stroke = underline.querySelector("path");
  const u0 = textWidth("System ", font);
  let d = `M${u0 + 6} 20`;
  for (let x = u0 + 6, i = 0; x < width - 30; x += 46, i += 1) d += ` q23 ${i % 2 ? 22 : -22} 46 0`;
  stroke.setAttribute("d", d);
  const caret = h("div", "caret", root);
  caret.style.height = "150px";
  const hazel = cursor(root, "squirrel", "Hazel", "#d9822b");

  const faces = PATTERNS.map(([, kind, color]) => {
    const disc = h("div", "disk", root);
    disc.style.cssText = `width:138px;height:138px;background:${tint(color)};overflow:hidden`;
    disc.face = critter(disc, kind, 128, { face: true });
    return disc;
  });

  return (t) => {
    const n = typedCount(sched, p(t, 0.75, 1.35, E.lin));
    title.textContent = text.slice(0, n);
    const swap = p(t, 3.0, 0.75, E.inOut);
    title.style.clipPath = `inset(-20% 0 -20% ${swap * 100}%)`;
    put(title, { x: x0, y: 540, anchor: "l" });

    const a = pop(t, 0.2, 3.2);
    put(tagA, { x: x0 + 8, y: 400, anchor: "l", s: a.s, o: a.o, r: -3 });
    const b = pop(t, 3.3, 4.7);
    put(tagB, { x: x0 + 8, y: 400, anchor: "l", s: b.s, o: b.o, r: -3 });

    const cx = x0 + textWidth(text.slice(0, n), font) + 10;
    const typingNow = t > 0.75 && t < 2.1;
    const caretOn = t > 0.4 && t < 2.7 && (typingNow || Math.floor(t * 2.6) % 2 === 0);
    put(caret, { x: cx, y: 540, o: caretOn ? 1 : 0, sy: spring(t, 0.4) });
    const arrive = p(t, 0, 0.7, E.outExpo);
    const leave = p(t, 2.5, 0.8, E.in);
    put(hazel, { x: lerp(1700, cx + 14, arrive) + leave * 900, y: lerp(980, 610, arrive) + leave * 260,
      anchor: "tl", o: 1 - p(t, 3.1, 0.2) });
    hazel.face.draw({ eyes: blink(t) });

    stroke.setAttribute("stroke-dashoffset", 1 - p(t, 2.15, 0.5, E.inOut));
    put(underline, { x: x0, y: 640, anchor: "l", o: (t > 2.15 ? 1 : 0) * (1 - p(t, 3.0, 0.2)) });

    faces.forEach((disc, i) => {
      const at = 3.0 + i * 0.07;
      const fall = Math.max(0, t - 4.65 - i * 0.03);
      const x = 960 + (i - 4.5) * 152;
      put(disc, { x, y: 540 + Math.sin(t * 4 - i * 0.6) * 9 + 2600 * fall * fall,
        s: spring(t, at), o: p(t, at, 0.08), r: fall * 160 * (i % 2 ? 1 : -1) });
      disc.face.draw({ eyes: t - at < 0.9 ? "happy" : blink(t, i * 0.7) });
    });
  };
}

/* ------------------------------------------------------- 2. The pitch and the game ----- */
function sceneGame(root, clip) {
  const win = clipWindow(root, clip, 1300);
  const [W, H] = win.size;
  const mk = (cls, html, color, kind, name) => {
    const line = h("div", cls, root, html);
    const sel = h("div", "sel", line, "<i></i><i></i><i></i><i></i>");
    sel.style.cssText = `position:absolute;inset:-6px -26px -2px;--chip:${color}`;
    return { line, sel, cur: cursor(root, kind, name, color) };
  };
  const l1 = mk("h-md", "Learn it by", "#2f8fd6", "goose", "Gus");
  const l2 = mk("h-lg", "running a zoo.", "#d9538a", "beaver", "Bea");
  const notes = [
    [h("div", "pill bad", root, "10 keepers asleep"), 330, 205, -5, 11.0],
    [h("div", "pill bad", root, "30 Owl calls for 6 questions"), 1570, 250, 4, 11.7],
    [h("div", "pill dark", root, "every missing pattern costs you"), 1500, 985, -3, 12.4],
  ];
  const ring = h("div", "ring", root);
  ring.style.cssText = "width:270px;height:270px";
  const tag = h("div", "pill", root, '<span class="num" style="--chip:#d9822b">01</span> Cache · Hazel is asleep');
  const FOCUS = [0.365, 0.5];

  const fly = (item, t, t0, from, to, r0) => {
    const k = p(t, t0, 0.8, E.outBack);
    const dt = Math.max(0, t - t0);
    const shrink = p(t, 7.2, 0.8, E.inOut);
    const x = lerp(from[0], to[0], k);
    const y = lerp(lerp(from[1], to[1], k), to[2], shrink);
    const r = lerp(r0, 0, p(t, t0, 0.8)) + Math.sin(dt * 17) * Math.exp(-dt * 5) * 5;
    const o = (t > t0 ? 1 : 0) * (1 - p(t, 10.2, 0.3));
    put(item.line, { x, y, r, s: lerp(1, 0.5, shrink), o });
    item.sel.style.opacity = 1 - p(t, t0 + 1.0, 0.2);
    const w = item.line.offsetWidth / 2 + 26;
    const away = p(t, t0 + 1.0, 0.9, E.inOut);
    put(item.cur, { x: x + w + away * 170, y: y + item.line.offsetHeight / 2 + away * 120, anchor: "tl",
      o: (t > t0 ? 1 : 0) * (1 - p(t, t0 + 1.5, 0.3)) });
    item.cur.face.draw({ eyes: blink(t, t0) });
  };

  return (t, pending) => {
    fly(l1, t, 5.3, [-500, 200], [960, 430, 100], -16);
    fly(l2, t, 5.6, [2500, 860], [960, 570, 172], 12);

    const rise = p(t, 7.3, 0.95, E.outExpo);
    const push = p(t, 10.2, 1.0, E.inOut);
    const zoom = p(t, 14.2, 1.1, E.inOut);
    const s = lerp(lerp(1, 1.1, push), 1.75, zoom);
    const cx = lerp(960, 960 - (FOCUS[0] - 0.5) * W * 1.75, zoom);
    const cy = lerp(lerp(lerp(1560, 650, rise), 560, push), 540 - (FOCUS[1] - 0.5) * H * 1.75, zoom);
    put(win, { x: cx, y: cy, s, r: lerp(3, 0, rise) });
    pending.push(win.show(1.6 + Math.max(0, t - 7.3)));

    for (const [el, x, y, r, at] of notes) {
      const a = pop(t, at, 14.0);
      put(el, { x, y, r: r + Math.sin(t * 2 + x) * 1.2, s: a.s, o: a.o });
    }
    put(ring, { x: 960, y: 540, s: spring(t, 15.1), o: p(t, 15.1, 0.1), r: t * 22 });
    const a = pop(t, 15.45);
    put(tag, { x: 960, y: 735, s: a.s, o: a.o, r: -2 });
  };
}

/* ------------------------------------------------------------- 3. Write the code -------- */
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
function paint(line) {
  return line.replace(TOKEN, (m, cm, kw, nb, self, fn) => {
    const cls = cm ? "cm" : kw ? "kw" : nb ? "nb" : self ? "self" : fn ? "fn" : "";
    return cls ? `<span class="${cls}">${esc(m)}</span>` : esc(m);
  });
}

function sceneCode(root, clip) {
  const WAKE = 26.6;
  const editor = h("div", "editor card", root);
  h("div", "bar", editor, '<b></b><b></b><b></b><img src="../assets/logos/python.svg"> levels/l01_cache/cache.py');
  const code = h("div", "code", editor);
  const term = h("div", "term", editor);
  const sched = typing(BODY, 3);
  const cmd = "python -m zoo test 1";

  const disk = h("div", "disk", root);
  disk.style.cssText = "width:410px;height:410px";
  const burst = h("div", "burst", root);
  burst.style.cssText = "width:100px;height:100px";
  const hazel = critter(root, "squirrel", 470);
  const tape = h("div", "tape", root);
  tape.style.width = "480px";
  const asleep = h("div", "pill", root, '<span class="num" style="--chip:#b9aec4">01</span> Cache · asleep');
  const awake = h("div", "pill", root, '<span class="num" style="--chip:#d9822b">01 CACHE</span> Cache hit: instant answer, 0 coins <span style="color:#3a9a50">✔</span>');
  awake.style.fontSize = "30px";
  const coins = Array.from({ length: 16 }, () => h("div", "coin", root));
  const live = clipWindow(root, clip, 540);
  const liveTag = h("div", "pill sm dark", root, "live in your zoo");
  const row = h("div", "", root);
  row.style.cssText = "display:flex;gap:22px;align-items:center";
  const rewards = [
    h("div", "pill good", row, 'Owl calls <span class="strike">30</span> → <b style="font-size:44px;line-height:1">6</b>'),
    h("div", "pill good", row, "repeat questions: instant"),
    h("div", "pill", row, '<span class="coin" style="width:34px;height:34px"></span> coins saved'),
  ];

  return (t, pending) => {
    const enter = spring(t, 17.15, 7, 9);
    put(editor, { x: 590, y: 500 + (1 - enter) * 120, o: p(t, 17.15, 0.2) });

    let html = `<span class="ln">${paint(HEAD)}</span>`;
    if (t < 18.8) {
      const k = p(t, 18.2, 0.35, E.inOut);
      html += `<span class="ln"><span class="todo" style="background-size:${k * 100}% 100%">${esc(TODO)}</span></span>`;
    } else {
      const n = typedCount(sched, p(t, 19.0, 5.9, E.lin));
      const lines = BODY.slice(0, n).split("\n");
      const idle = n === 0 || n === BODY.length;
      const caretOn = t < 25.3 && (!idle || Math.floor(t * 2.6) % 2 === 0);
      lines.forEach((line, i) => {
        const last = i === lines.length - 1;
        html += `<span class="ln${last && t < 25.3 ? " cur" : ""}">${paint(line)}${last && caretOn ? '<span class="c"></span>' : ""}</span>`;
      });
    }
    if (code.innerHTML !== html) code.innerHTML = html;

    term.style.transform = `translateY(${lerp(100, 0, p(t, 25.2, 0.35))}px)`;
    const typed = cmd.slice(0, Math.round(p(t, 25.45, 0.55, E.lin) * cmd.length));
    const pass = t > 26.15 ? `<span class="ok" style="display:inline-block;transform:scale(${spring(t, 26.15)})">PASS</span> 01 Cache: every test is green` : "";
    const termHtml = `<span><span style="color:#58c96c">$</span> ${typed}</span>${pass}`;
    if (term.innerHTML !== termHtml) term.innerHTML = termHtml;

    // Hazel: asleep behind caution tape, then the tests pass and she wakes up.
    const dt = t - WAKE;
    const side = spring(t, 17.4, 7, 9);
    const hx = 1500 + (1 - side) * 700;
    put(disk, { x: hx, y: 400 });
    disk.style.background = dt > 0 ? "#ffe6c2" : "#ece6f0";
    const hop = dt > 0 && dt < 1.3 ? Math.abs(Math.sin((dt * Math.PI) / 0.42)) * 150 * Math.exp(-dt * 1.7) : 0;
    put(hazel, { x: hx, y: 380 });
    hazel.draw(dt < 0
      ? { eyes: "asleep", sleep: true, time: t, squash: Math.sin(t * 1.7) * 0.018 }
      : { eyes: dt < 1.7 ? "happy" : blink(t), lift: hop, time: t, squash: hop < 4 && dt < 1.3 ? 0.05 : 0 });
    const snap = p(t, WAKE, 0.55, E.in);
    put(tape, { x: hx - snap * 260, y: 575 + snap * 700, r: -5 - snap * 70, o: 1 - p(t, WAKE + 0.45, 0.1) });
    put(burst, { x: hx, y: 400, s: lerp(1, 7.5, p(t, WAKE, 0.55)), o: dt > 0 ? 1 - p(t, WAKE, 0.55) : 0 });
    const a = pop(t, 17.7, WAKE);
    put(asleep, { x: hx, y: 150, s: a.s, o: a.o, r: -2 });
    const b = pop(t, WAKE + 0.2);
    put(awake, { x: 1490, y: 150, s: b.s, o: b.o, r: -2 });
    coins.forEach((coin, i) => {
      const ang = -Math.PI * (0.08 + 0.84 * rnd(i + 2));
      const v = 520 + 620 * rnd(i + 40);
      const d = Math.max(0, dt);
      put(coin, { x: 1500 + Math.cos(ang) * v * d, y: 380 + Math.sin(ang) * v * d + 1100 * d * d,
        s: spring(t, WAKE), o: dt > 0 ? 1 - p(t, WAKE + 0.75, 0.3) : 0 });
    });

    const l = pop(t, WAKE + 0.9);
    put(live, { x: 1500, y: 800, s: l.s, o: l.o, r: 2 });
    if (dt > 0.8) pending.push(live.show(3 + (dt - 0.8)));
    const lt = pop(t, WAKE + 1.2);
    put(liveTag, { x: 1290, y: 652, s: lt.s, o: lt.o, r: -5 });

    put(row, { x: 100, y: 950, anchor: "l" });
    rewards.forEach((el, i) => {
      const r = pop(t, 28.2 + i * 0.32);
      el.style.transform = `scale(${r.s}) rotate(${[-2, 1.5, -1][i]}deg)`;
      el.style.opacity = r.o;
    });
  };
}

/* ----------------------------------------------------------- 4. Under the hood ---------- */
function sceneArch(root) {
  const QUESTIONS = [0, 1, 0, 2, 3, 1, 0, 4, 2, 3, 1, 5, 0, 2, 4, 1, 3, 5, 0, 2, 1, 4, 3, 5, 0, 1, 2, 3, 4, 5];
  const COLORS = PATTERNS.slice(0, 6).map((x) => x[2]);
  const T1 = 32.1;
  const SWITCH = 36.7;
  const T2 = 38.0;
  const GAP = 0.115;

  const wires = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  wires.setAttribute("class", "wires");
  root.appendChild(wires);
  const wire = () => wires.appendChild(document.createElementNS("http://www.w3.org/2000/svg", "line"));
  const wVA = wire();
  const wAS = wire();
  const wAR = wire();

  const node = (inner, label, sub) => {
    const el = h("div", "node card", root, inner);
    const text = h("div", "node-label", root, `${label}<small>${sub}</small>`);
    return { el, text };
  };
  const nV = node("", "Visitors", "30 questions");
  const visitor = critter(nV.el, "rabbit", 150, { face: true });
  const nA = node('<img src="../assets/logos/fastapi.svg">', "API", "FastAPI");
  const nS = node('<img src="../assets/logos/postgresql.svg">', "Source of truth", "LLM · database · slow");
  const owlBadge = h("div", "disk", root);
  owlBadge.style.cssText = "width:92px;height:92px;background:#f6e3c2;overflow:hidden";
  const owl = critter(owlBadge, "owl", 86, { face: true });
  const nR = node('<img src="../assets/logos/redis.svg">', "Redis", "cache · TTL");
  const slots = COLORS.map(() => h("div", "slot", root));
  const hitTag = h("div", "pill sm good", root, "hit: instant");
  const missTag = h("div", "pill sm", root, "miss: load once, set + TTL");

  const tag = h("div", "pill sm dark", root, "under the hood");
  const titleA = h("div", "h-sm", root, "Without a cache");
  const titleB = h("div", "h-sm", root, 'With <span style="color:#e0372c">Redis</span>');
  const big = h("div", "big", root);
  const bigLabel = h("div", "h-xs", root, "Owl calls");
  const hits = h("div", "pill good", root);
  const barLabel = h("div", "label", root, "answer time");
  const bar = h("div", "bar-fill", root);
  const barWord = h("div", "label", root);

  // Each request is a list of legs between named points, so any frame can ask "where is it now?".
  const first = new Set();
  const legs1 = [["V", "A", 0.25], ["A", "S", 0.5], ["S", "S", 0.3], ["S", "A", 0.35], ["A", "V", 0.25]];
  const legsHit = [["V", "A", 0.25], ["A", "R", 0.16], ["R", "R", 0.08], ["R", "A", 0.16], ["A", "V", 0.25]];
  const legsMiss = [["V", "A", 0.25], ["A", "R", 0.16], ["R", "A", 0.16], ["A", "S", 0.5], ["S", "S", 0.3],
    ["S", "A", 0.35], ["A", "R", 0.16], ["R", "A", 0.16], ["A", "V", 0.25]];
  const requests = [];
  QUESTIONS.forEach((q, i) => requests.push({ q, start: T1 + i * GAP, legs: legs1, call: 0.75, phase: 1 }));
  QUESTIONS.forEach((q, i) => {
    const miss = !first.has(q);
    first.add(q);
    requests.push({ q, start: T2 + i * GAP, legs: miss ? legsMiss : legsHit, phase: 2,
      call: miss ? 1.07 : null, hit: miss ? null : 0.41, stored: miss ? 1.88 : null });
  });
  for (const r of requests) {
    r.el = h("div", "dot", root);
    r.el.style.background = COLORS[r.q];
    r.total = r.legs.reduce((sum, leg) => sum + leg[2], 0);
  }

  return (t) => {
    const two = p(t, SWITCH, 0.8, E.inOut);
    const P = { V: [830, 540], A: [1160, 540], S: [1620, lerp(540, 790, two)],
      R: [1620, lerp(-260, 250, spring(t, SWITCH + 0.3, 6, 9))] };
    const line = (el, a, b, o = 1) => {
      el.setAttribute("x1", P[a][0] + 105); el.setAttribute("y1", P[a][1] + (P[b][1] - P[a][1]) * 0.24);
      el.setAttribute("x2", P[b][0] - 105); el.setAttribute("y2", P[b][1] - (P[b][1] - P[a][1]) * 0.24);
      el.style.opacity = o;
      el.setAttribute("stroke-dashoffset", -t * 40);
    };
    line(wVA, "V", "A", p(t, 31.6, 0.3));
    line(wAS, "A", "S", p(t, 31.8, 0.3));
    line(wAR, "A", "R", p(t, SWITCH + 0.8, 0.3));

    const place = (n, key, at, extra = 0) => {
      const s = spring(t, at);
      put(n.el, { x: P[key][0], y: P[key][1], s: s * (1 + extra), o: p(t, at, 0.1) });
      put(n.text, { x: P[key][0], y: P[key][1] + 150, o: p(t, at + 0.15, 0.25) });
    };
    const busy = t > T1 + 0.7 && t < SWITCH ? Math.sin(t * 30) * 0.02 : 0;
    place(nV, "V", 31.3);
    place(nA, "A", 31.45);
    place(nS, "S", 31.6, busy);
    put(owlBadge, { x: P.S[0] + 92, y: P.S[1] - 92, s: spring(t, 31.9), o: p(t, 31.9, 0.1), r: 8 });
    put(nR.el, { x: P.R[0], y: P.R[1], o: t > SWITCH + 0.3 ? 1 : 0 });
    put(nR.text, { x: P.R[0], y: P.R[1] + 190, o: p(t, SWITCH + 0.9, 0.25) });
    visitor.draw({ eyes: t < SWITCH ? "sad" : t > T2 + 0.6 ? "happy" : blink(t) });
    owl.draw({ eyes: t > T1 + 0.7 && t < SWITCH ? "sick" : blink(t, 1) });

    let calls = 0;
    let hitCount = 0;
    const stored = new Set();
    const phase = t < SWITCH + 0.9 ? 1 : 2;
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
      put(r.el, { x: lerp(P[leg[0]][0], P[leg[1]][0], k), y: lerp(P[leg[0]][1], P[leg[1]][1], k) + (r.q - 2.5) * 5 });
    }
    slots.forEach((slot, i) => {
      slot.style.background = stored.has(i) ? COLORS[i] : "#fff";
      put(slot, { x: P.R[0] - 85 + i * 34, y: P.R[1] + 128, o: p(t, SWITCH + 0.9, 0.2) });
    });
    const ht = pop(t, T2 + 0.5);
    put(hitTag, { x: 1300, y: 330, s: ht.s, o: ht.o, r: -4 });
    const mt = pop(t, T2 + 1.2);
    put(missTag, { x: 1250, y: 770, s: mt.s, o: mt.o, r: 3 });

    // Left column: one number tells the story.
    const tg = pop(t, 31.2);
    put(tag, { x: 110, y: 215, anchor: "l", s: tg.s, o: tg.o, r: -3 });
    const sw = p(t, SWITCH, 0.4, E.inOut);
    put(titleA, { x: 110, y: 320 - sw * 50, anchor: "l", o: p(t, 31.3, 0.3) * (1 - sw) });
    put(titleB, { x: 110, y: 320 + (1 - sw) * 50, anchor: "l", o: sw });
    big.textContent = calls;
    big.style.color = phase === 1 ? (calls >= 30 ? "#e5484d" : "#4b3757") : "#3a9a50";
    const bump = phase === 1 ? spring(t, 31.5) : spring(t, SWITCH + 0.9);
    put(big, { x: 104, y: 540, anchor: "l", s: bump, o: p(t, 31.5, 0.2) });
    put(bigLabel, { x: 110, y: 690, anchor: "l", o: p(t, 31.7, 0.3) });
    hits.innerHTML = `<b>${hitCount}</b> answered from the cache`;
    const hp = pop(t, T2 + 0.45);
    put(hits, { x: 110, y: 790, anchor: "l", s: hp.s, o: hp.o, r: -1.5 });
    const grow = p(t, 32.6, 0.9, E.out);
    const shrink = p(t, T2 + 0.4, 0.9, E.inOut);
    const w = lerp(540, 74, shrink) * grow;
    bar.style.width = `${Math.max(34, w)}px`;
    bar.style.background = shrink > 0.5 ? "#58c96c" : "#ff8fab";
    put(barLabel, { x: 110, y: 890, anchor: "l", o: p(t, 32.5, 0.3) });
    put(bar, { x: 110, y: 945, anchor: "l", o: p(t, 32.6, 0.2) });
    barWord.textContent = shrink > 0.5 ? "instant" : "slow";
    put(barWord, { x: 110 + w + 22, y: 945, anchor: "l", o: p(t, 33.4, 0.3) });
  };
}

/* --------------------------------------------------------- 5. The ten patterns --------- */
function scenePatterns(root) {
  const title = h("div", "h-sm", root, "10 patterns you build yourself");
  const cards = PATTERNS.map(([name, kind, color], i) => {
    const el = h("div", "badge card", root);
    el.face = critter(el, kind, 92, { face: true });
    const text = h("div", "", el);
    el.n = h("div", "n", text, String(i + 1).padStart(2, "0"));
    h("div", "t", text, name);
    el.color = color;
    return el;
  });
  const row = h("div", "", root);
  row.style.cssText = "display:flex;gap:22px;align-items:center";
  const made = [h("div", "label", row, "made for"), h("div", "pill", row, "system design interviews"),
    h("div", "pill", row, "juniors"), h("div", "pill", row, "anyone who learns by breaking things")];

  return (t) => {
    const tt = pop(t, 43.7);
    put(title, { x: 960, y: 170, s: lerp(0.8, 1, tt.s), o: tt.o });
    cards.forEach((el, i) => {
      const at = 43.9 + i * 0.05;
      const wake = 45.0 + i * 0.19;
      const on = t >= wake;
      const hop = Math.sin(Math.PI * clamp((t - wake) / 0.36));
      el.style.background = on ? "#fff" : "#f1ecf4";
      el.style.borderStyle = on ? "solid" : "dashed";
      el.style.borderColor = on ? "#4b3757" : "#b9aec4";
      el.style.color = on ? "#4b3757" : "#a294b0";
      el.n.style.color = on ? el.color : "#b9aec4";
      el.face.style.background = on ? tint(el.color) : "#e4dcea";
      el.face.draw(on ? { eyes: t - wake < 1 ? "happy" : blink(t, i) } : { eyes: "asleep" });
      put(el, { x: 264 + (i % 5) * 348, y: 400 + Math.floor(i / 5) * 190 - (on ? hop * 30 : 0),
        s: spring(t, at) * (1 + (on ? hop * 0.07 : 0)), o: p(t, at, 0.1), r: on ? hop * (i % 2 ? 3 : -3) : 0 });
    });
    put(row, { x: 960, y: 810 });
    made.forEach((el, i) => {
      const a = pop(t, 47.0 + i * 0.28);
      el.style.transform = `scale(${a.s}) rotate(${[0, -2, 2, -1][i]}deg)`;
      el.style.opacity = a.o;
    });
  };
}

/* ------------------------------------------------------- 6. Tagline and sign off ------- */
function sceneEnd(root) {
  const WORDS = [["caching", "#d9822b", 49.3], ["rate limiting", "#2f8fd6", 50.05],
    ["idempotency", "#7a62d9", 50.8], ["system design", "#3a9a50", 51.55]];
  const line = h("div", "", root);
  line.style.cssText = "display:flex;align-items:center;gap:26px;font-size:78px;font-weight:800";
  h("span", "", line, "Learn");
  const chip = h("span", "swap", line);
  h("span", "", line, "by keeping a zoo alive.");
  const words = WORDS.map(([word]) => h("span", "", chip, word));
  const widths = WORDS.map(([word]) => textWidth(word, '800 78px "Baloo 2"') + 52);

  const logo = h("div", "disk", root);
  logo.style.cssText = "width:230px;height:230px;background:#f6e3c2;overflow:hidden";
  const owl = critter(logo, "owl", 220, { face: true });
  const mark = h("div", "wordmark", root);
  mark.style.cssText = "font-size:210px;font-weight:800;line-height:1";
  const letters = [..."Zoo Ops"].map((ch) => h("span", "", mark, ch === " " ? "&nbsp;" : ch));
  const cmd = h("div", "pill dark mono", root);
  cmd.style.fontSize = "36px";
  const foot = h("div", "label", root, "free and open source · github.com/aliamrrr/zoo-ops");
  const crowd = ["squirrel", "goose", "fox", "cat", "meerkat", "panda", "mole", "beaver", "dog", "canary", "penguin"]
    .map((kind) => critter(root, kind, 200));

  return (t) => {
    let idx = 0;
    WORDS.forEach((w, i) => { if (t >= w[2]) idx = i; });
    const k = p(t, WORDS[idx][2], 0.32, E.out);
    const prev = Math.max(0, idx - 1);
    chip.style.width = `${lerp(widths[prev], widths[idx], idx ? E.outBack(clamp((t - WORDS[idx][2]) / 0.32)) : 1)}px`;
    chip.style.background = WORDS[idx][1];
    chip.style.transform = `rotate(${-2 + Math.sin((t - WORDS[idx][2]) * 20) * Math.exp(-(t - WORDS[idx][2]) * 7) * 3}deg)`;
    words.forEach((el, i) => {
      const y = i === idx ? lerp(idx ? 104 : 0, 0, k) : i === prev && idx ? lerp(0, -104, k) : 200;
      el.style.transform = `translateY(${y}px)`;
    });
    const up = p(t, 52.7, 0.35, E.in);
    put(line, { x: 960, y: 540 - up * 80, s: lerp(0.9, 1, spring(t, 49.2)), o: p(t, 49.2, 0.15) * (1 - up) });

    put(logo, { x: 960, y: 330, s: spring(t, 53.0), o: p(t, 53.0, 0.1) });
    owl.draw({ eyes: t < 54.2 ? "happy" : blink(t) });
    put(mark, { x: 960, y: 565, o: t > 53.1 ? 1 : 0 });
    letters.forEach((el, i) => {
      const at = 53.15 + i * 0.055;
      el.style.transform = `scale(${spring(t, at)}) rotate(${(1 - p(t, at, 0.4)) * (i % 2 ? 24 : -24)}deg)`;
      el.style.opacity = p(t, at, 0.08);
    });
    const c = pop(t, 54.1);
    const typed = "python -m zoo play".slice(0, Math.round(p(t, 54.35, 0.7, E.lin) * 18));
    cmd.innerHTML = `<span style="color:#58c96c">$</span> ${typed}<span style="opacity:${t > 55.05 && Math.floor(t * 2.6) % 2 ? 0 : 1}">▌</span>`;
    put(cmd, { x: 960, y: 745, s: c.s, o: c.o });
    put(foot, { x: 960, y: 840, o: p(t, 55.3, 0.4) });
    crowd.forEach((el, i) => {
      const at = 53.7 + i * 0.07;
      const wave = Math.max(0, Math.sin((t - 56.2) * 9 - i * 0.55)) * (t > 56.2 && t < 57.3 ? 1 : 0);
      put(el, { x: 110 + i * 170, y: lerp(1300, 1022, spring(t, at, 7, 10)) - wave * 34 + Math.sin(t * 2.4 + i) * 5 });
      el.draw({ eyes: wave > 0.2 ? "happy" : blink(t, i * 0.9), time: t });
    });
  };
}

/* ------------------------------------------------------------------- Timeline ---------- */
async function init() {
  await document.fonts.load('800 100px "Baloo 2"');
  await document.fonts.load('700 100px "Baloo 2"');
  await document.fonts.load('800 30px "Nunito"');
  await document.fonts.load('500 30px "JetBrains Mono"');
  await document.fonts.load('700 30px "JetBrains Mono"');
  const [before, after] = await Promise.all([loadClip("before"), loadClip("after")]);

  scene(0, 5.3, sceneTitle);
  scene(5.1, 17.2, (root) => sceneGame(root, before));
  scene(17.0, 31.2, (root) => sceneCode(root, after));
  scene(31.0, 43.7, sceneArch);
  scene(43.5, 49.2, scenePatterns);
  scene(49.0, DURATION + 1, sceneEnd);

  /** Render the frame at time t (seconds). Resolves once every image it needs is decoded. */
  window.seek = async (t) => {
    const pending = [];
    stage.style.backgroundPosition = `${t * 7}px ${t * 4}px`;
    for (const sc of scenes) {
      const on = t >= sc.a && t < sc.b;
      sc.root.style.display = on ? "" : "none";
      if (!on) continue;
      const kin = sc.a === 0 ? 1 : p(t, sc.a, 0.4, E.out);
      const kout = p(t, sc.b - 0.3, 0.3, E.in);
      sc.root.style.opacity = kin * (1 - kout);
      sc.root.style.transform = `scale(${lerp(0.97, 1, kin) * lerp(1, 1.05, kout)})`;
      sc.root.style.filter = kout > 0.02 ? `blur(${kout * 18}px)` : "";
      sc.update(t, pending);
    }
    await Promise.all(pending.filter(Boolean));
  };
  window.FILM = { duration: DURATION, fps: FPS };

  // Preview: ?play runs in real time; ?t=12.5 shows one frame. Space pauses, arrows scrub.
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
      if (e.key === "ArrowRight") t += e.shiftKey ? 1 : 1 / FPS;
      if (e.key === "ArrowLeft") t -= e.shiftKey ? 1 : 1 / FPS;
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
