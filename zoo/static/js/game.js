import { api } from "./api.js";
import { critterCanvas } from "./art.js";
import { SYSTEMS, SYSTEM_IDS } from "./systems.js";

export const SHIFT_SECONDS = 180;
export const PATIENCE = 26;
export const HUNGRY_AT = 25;
const TICK_MS = 100;
const START_COINS = 20;
const START_REP = 70;
const MAX_QUEUE = 6;
const HUNGER_DECAY = 1.15;
const HUNGER_PER_GRAM = 0.8;
const STUFFED_AT = 125;
const SICK_SECONDS = 12;
const DB_LAG_MS = 1000;
const PAGER_LEAD = 5;
const STORM_SECONDS = 25;
const DIRT_EVERY = 15;
const ADOPTION_WINDOW = 16;
const STAR_SCORES = [150, 350, 550];
const BEST_KEY = "zoo-ops-best-score";

export const ANIMALS = [
  { id: "lion", name: "Leo", kind: "lion" },
  { id: "otter", name: "Pebble", kind: "otter" },
  { id: "penguin", name: "Waddle", kind: "penguin" },
  { id: "miso", name: "Miso", kind: "cat" },
];
const VISITOR_KINDS = ["hedgehog", "rabbit", "frog"];
export const INCIDENTS = [
  { at: 40, kind: "pigeons", label: "Pigeons", soon: "a pigeon swarm is coming" },
  { at: 72, kind: "storm", label: "Storm", soon: "a storm is coming" },
  { at: 108, kind: "raccoon", label: "Intruder", soon: "someone is at the staff door" },
  { at: 135, kind: "release", label: "Release", soon: "kiosk v2 is rolling out" },
];
const ADOPTIONS = [28, 88, 150];
const NOTE_SYSTEMS = [
  [/cache/i, "01"],
  [/fallback|never answered|every model|kiosk code/i, "03"],
  [/idempotency|unique|food bowl/i, "04"],
  [/sse/i, "08"],
];

const $ = (selector) => document.querySelector(selector);
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const random = (min, max) => min + Math.random() * (max - min);
const pick = (items) => items[Math.floor(Math.random() * items.length)];

export function el(tag, attributes = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attributes)) {
    if (key === "text") node.textContent = value;
    else node.setAttribute(key, value);
  }
  node.append(...children);
  return node;
}

/** The colored "04 Idempotency" tag used everywhere a pattern is named. */
export function patternChip(id, tag = "span") {
  const chip = el(tag, { class: "pattern-chip", style: `--chip:${SYSTEMS[id].color}` }, [
    el("b", { text: id }),
    document.createTextNode(SYSTEMS[id].label),
  ]);
  if (tag === "button") chip.type = "button";
  return chip;
}

function nearestRank(values, p) {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.max(0, Math.ceil((p / 100) * sorted.length) - 1)];
}

function readBest() {
  try {
    return Number(localStorage.getItem(BEST_KEY)) || 0;
  } catch {
    return 0;
  }
}

function writeBest(score) {
  try {
    localStorage.setItem(BEST_KEY, String(score));
  } catch {
    /* private mode: the best score is simply not remembered */
  }
}

/**
 * The rules of the shift. It owns the state, the HUD, the journal and the overlays, and
 * reports what happens through `events`, a queue the world drains to animate and play sounds.
 * A "moment" event is a pattern doing (or failing to do) its job at a place in the zoo.
 */
export class Game {
  constructor({ questions, onOpenStation, onMoment, onShiftStart }) {
    this.questions = Object.entries(questions);
    this.onOpenStation = onOpenStation;
    this.onMoment = onMoment;
    this.onShiftStart = onShiftStart;
    this.systems = {};
    this.state = "idle";
    this.timer = null;
    this.nextId = 1;
    $("#pause").addEventListener("click", () => this.togglePause());
    this.reset();
    this.showIntro();
  }

  /* Systems */

  online(id) {
    return this.systems[id]?.status === "healthy";
  }

  onlineCount() {
    return SYSTEM_IDS.filter((id) => this.online(id)).length;
  }

  setSystems(systems) {
    const before = this.systems;
    this.systems = systems;
    if (this.state === "running" || this.state === "paused") {
      for (const [id, system] of Object.entries(systems)) {
        const was = before[id]?.status;
        if (was && was !== "healthy" && system.status === "healthy") {
          this.log(`Good news: the ${SYSTEMS[id].name} is back online.`, "good", id);
        } else if (was === "healthy" && system.status !== "healthy") {
          this.log(`The ${SYSTEMS[id].name} just went down.`, "bad", id);
        }
      }
    }
    this.renderPins();
    if (this.state === "idle") this.showIntro();
  }

  /* Events for the world */

  emit(id, good, text, anchor = null, cooldown = 0) {
    this.stats[id][good ? "good" : "bad"] += 1;
    this.onMoment?.(id, good, this.stats[id]);
    const key = `${id}:${good}`;
    if (cooldown && this.t < (this.cooldowns[key] || 0)) return;
    this.cooldowns[key] = this.t + cooldown;
    this.events.push({ type: "moment", id, good, text, anchor });
  }

  fx(type, data = {}) {
    this.events.push({ type, ...data });
  }

  sfx(name) {
    this.events.push({ type: "sfx", name });
  }

  earn(amount, anchor) {
    this.coins += amount;
    if (amount) this.events.push({ type: "coins", amount, anchor });
  }

  /* Shift lifecycle */

  reset() {
    this.t = 0;
    this.coins = START_COINS;
    this.rep = START_REP;
    this.served = 0;
    this.lost = 0;
    this.waits = [];
    this.blame = {};
    this.notes = new Set();
    this.events = [];
    this.timers = [];
    this.cooldowns = {};
    this.stats = Object.fromEntries(SYSTEM_IDS.map((id) => [id, { good: 0, bad: 0 }]));
    this.visitors = [];
    this.departures = [];
    this.bubbles = {};
    this.nextVisitor = 2;
    this.nextDirt = 20;
    this.kioskBusy = false;
    this.trip = null;
    this.speech = { text: "", state: "idle" };
    this.askedTopics = new Set();
    this.telemetryNoted = false;
    this.jammedUntil = 0;
    this.pigeonsEvent = null;
    this.stormUntil = 0;
    this.raccoonEvent = null;
    this.releaseEvent = null;
    this.brokenReleaseUntil = 0;
    this.adoption = null;
    this.adoptionResult = null;
    this.diggingUntil = 0;
    this.pagerUntil = 0;
    this.incidents = INCIDENTS.map((incident) => ({ ...incident, paged: false, done: false }));
    this.adoptions = [...ADOPTIONS];
    this.pens = ANIMALS.map((animal) => ({
      ...animal, hunger: 70, sick: 0, dirty: false, dirtSpot: null, busy: false,
      cleanAt: null, antsSince: null, tag: "", tagUntil: 0, fedAt: -99,
    }));
    $("#log").replaceChildren();
    $("#pager").hidden = true;
    this.renderPins();
    this.renderHud();
  }

  async start() {
    this.reset();
    await api.reset().catch(() => null);
    this.state = "running";
    $("#overlay").hidden = true;
    this.onShiftStart?.();
    this.sfx("good");
    this.log(`The gates open. ${this.onlineCount()} of 10 backend systems are online today.`);
    this.timer = setInterval(() => this.tick(TICK_MS / 1000), TICK_MS);
  }

  pause() {
    if (this.state !== "running") return;
    this.state = "paused";
    clearInterval(this.timer);
    this.overlay([
      el("h1", { text: "Paused" }),
      el("p", { class: "muted",
        text: "The zoo waits for you. Saved a level file? The game picks it up when you come back." }),
    ], [["Resume", () => this.resume(), "button-primary"]]);
  }

  resume() {
    if (this.state !== "paused") return;
    this.state = "running";
    $("#overlay").hidden = true;
    this.timer = setInterval(() => this.tick(TICK_MS / 1000), TICK_MS);
  }

  togglePause() {
    if (this.state === "running") this.pause();
    else if (this.state === "paused") this.resume();
  }

  finish(reason, won) {
    clearInterval(this.timer);
    this.state = "over";
    const score = Math.max(0, Math.round(this.coins)) + Math.round(this.rep) * 3 + this.served * 2;
    const stars = STAR_SCORES.filter((needed) => score >= needed).length;
    const best = readBest();
    if (score > best) writeBest(score);
    this.sfx(won ? "win" : "lose");
    if (won) this.fx("confetti");

    const worst = Object.entries(this.blame).sort((a, b) => b[1] - a[1]).slice(0, 3);
    const lessons = worst.length
      ? el("ul", { class: "lessons" }, worst.map(([id, cost]) => {
        const chip = patternChip(id, "button");
        chip.addEventListener("click", () => this.onOpenStation(id));
        return el("li", {}, [chip, el("span", { text: `cost you ${Math.round(cost)} points` })]);
      }))
      : el("p", { class: "muted", text: "No system let you down. Flawless backend." });
    this.overlay([
      el("p", { class: "eyebrow", text: reason }),
      el("div", { class: "stars", "aria-label": `${stars} of 3 stars` }, [0, 1, 2].map((i) =>
        el("span", { class: "star", "data-on": String(i < stars) }))),
      el("div", { class: "score", text: String(score) }),
      el("p", { class: "muted", text: score > best ? "New best score!" : `Best so far: ${best}` }),
      el("dl", { class: "stats" }, [
        this.stat("Coins", Math.round(this.coins)),
        this.stat("Reputation", Math.round(this.rep)),
        this.stat("Visitors served", `${this.served} / ${this.served + this.lost}`),
      ]),
      el("h2", { class: "overlay-title", text: "What cost you the most" }),
      lessons,
    ], [["Play again", () => this.start(), "button-primary"]]);
  }

  stat(label, value) {
    return el("div", {}, [el("dt", { text: label }), el("dd", { text: String(value) })]);
  }

  showIntro() {
    const known = Object.keys(this.systems).length > 0;
    const cast = el("div", { class: "cast" }, ["rabbit", "squirrel", "owl", "fox", "penguin"].map(
      (kind, i) => critterCanvas(kind, i === 2 ? 96 : 68)));
    const dots = el("div", { class: "system-dots" }, SYSTEM_IDS.map((id) =>
      el("i", { "data-on": String(this.online(id)), style: `--chip:${SYSTEMS[id].color}`,
        title: `${id} ${SYSTEMS[id].label}` })));
    this.overlay([
      cast,
      el("h1", { class: "logo", text: "Zoo Ops" }),
      el("p", { class: "tagline", text: "One shift. Three minutes. Keep everyone happy." }),
      el("ul", { class: "howto" }, [
        el("li", { text: "Click a visitor to send their question to the Owl." }),
        el("li", { text: "Click an animal to feed it. Once is enough!" }),
        el("li", { text: "Click dirt to clean it, and the pink cottage when families wait." }),
      ]),
      el("div", { class: "systems-line" }, [
        dots,
        el("span", { text: known
          ? `${this.onlineCount()} of 10 backend patterns built. Each one you code wakes up a keeper.`
          : "Running the morning backend check..." }),
      ]),
    ], [["Open the gates", () => this.start(), "button-primary button-big"]], !known);
  }

  overlay(children, actions, disabled = false) {
    const buttons = actions.map(([label, action, style]) => {
      const button = el("button", { class: `button ${style}`, type: "button", text: label });
      button.disabled = disabled;
      button.addEventListener("click", action);
      return button;
    });
    $("#overlay-card").replaceChildren(...children, el("div", { class: "overlay-actions" }, buttons));
    $("#overlay").hidden = false;
    buttons[0]?.focus();
  }

  /* Main loop */

  tick(dt) {
    if (this.state !== "running") return;
    this.t += dt;

    if (!this.telemetryNoted && this.t > 3) {
      this.telemetryNoted = true;
      if (this.online("05")) this.emit("05", true, "Telemetry on: bars, p95, forecast");
      else this.emit("05", false, "No telemetry: bars and forecast hidden");
    }
    for (const timer of this.timers.filter((item) => this.t >= item.at)) timer.run();
    this.timers = this.timers.filter((item) => this.t < item.at);
    if (this.t >= this.nextVisitor) {
      this.spawnVisitor();
      this.nextVisitor = this.t + random(3.2, 5.4) * (this.t > 120 ? 0.85 : 1);
    }
    for (const visitor of [...this.visitors]) {
      if (visitor.engaged) continue;
      visitor.patience -= dt;
      if (visitor.patience <= 0) this.visitorGivesUp(visitor);
    }
    this.departures = this.departures.filter((departure) => this.t - departure.at < 7);
    this.tickPens(dt);
    this.tickIncidents();
    this.tickAdoption();

    this.rep = Math.min(100, this.rep);
    if (this.rep <= 0) {
      this.rep = 0;
      this.renderHud();
      this.finish("The zoo lost the trust of its visitors", false);
      return;
    }
    if (this.t >= SHIFT_SECONDS) {
      this.closing();
      this.renderHud();
      this.finish("Shift over", true);
      return;
    }
    this.renderHud();
  }

  tickPens(dt) {
    if (this.t >= this.nextDirt) {
      const clean = this.pens.filter((pen) => !pen.dirty);
      if (clean.length) {
        const pen = pick(clean);
        pen.dirty = true;
        pen.dirtSpot = { x: random(0.25, 0.75), y: random(0.5, 0.8) };
        if (this.online("08")) {
          pen.cleanAt = this.t + 4.5;
          pen.antsSince = this.t;
          this.emit("08", true, `Background job: the ants clean ${pen.name}'s pen`);
        } else {
          this.emit("08", false, "No workers: clean it by hand", `pen:${pen.id}`);
          this.log(`${pen.name}'s pen is dirty. Click the dirt to clean it by hand.`, "warn", "08");
        }
      }
      this.nextDirt = this.t + DIRT_EVERY;
    }
    for (const pen of this.pens) {
      if (pen.sick > 0) {
        pen.sick -= dt;
        if (pen.sick <= 0) this.log(`${pen.name} feels better.`);
      }
      pen.hunger = Math.max(0, pen.hunger - HUNGER_DECAY * dt);
      if (pen.hunger < HUNGRY_AT) this.rep -= 0.25 * dt;
      if (pen.dirty) this.hurt(this.online("08") ? null : "08", 0.12 * dt);
      if (pen.dirty && pen.cleanAt !== null && this.t >= pen.cleanAt) {
        pen.dirty = false;
        pen.cleanAt = null;
        pen.antsSince = null;
        this.fx("clean", { pen: pen.id });
      }
    }
  }

  tickIncidents() {
    for (const incident of this.incidents) {
      if (!incident.paged && this.online("05") && this.t >= incident.at - PAGER_LEAD) {
        incident.paged = true;
        this.page(incident.soon);
      }
      if (!incident.done && this.t >= incident.at) {
        incident.done = true;
        if (!this.online("05")) this.emit("05", false, "No alert: you did not see it coming");
        this[incident.kind]();
        this.renderPins();
      }
    }
    if (this.pagerUntil && this.t >= this.pagerUntil) {
      this.pagerUntil = 0;
      $("#pager").hidden = true;
    }
    if (this.stormUntil && this.t >= this.stormUntil) {
      this.stormUntil = 0;
      this.log("The storm is over. The bridge to the Owl is open again.");
    }
  }

  tickAdoption() {
    if (this.adoptions.length && this.t >= this.adoptions[0]) {
      this.adoptions.shift();
      this.adoption = { deadline: this.t + ADOPTION_WINDOW, since: this.t, pending: false };
      this.sfx("pop");
      this.log("Two families want to adopt Pixel the kitten. Click the pink cottage.", "warn");
    }
    if (this.adoption && !this.adoption.pending && this.t >= this.adoption.deadline) {
      this.adoption = null;
      this.hurt(null, 4);
      this.log("The families gave up waiting at the adoption office.", "bad");
    }
  }

  /* Visitors and the Owl kiosk */

  spawnVisitor() {
    const waiting = this.visitors.filter((visitor) => visitor.state === "waiting");
    if (waiting.length >= MAX_QUEUE) {
      this.hurt(this.online("01") ? null : "01", 1);
      this.lost += 1;
      this.say("goose", "The line is full!", 2);
      return;
    }
    const [topic, question] = pick(this.questions);
    this.visitors.push({
      id: this.nextId++, kind: pick(VISITOR_KINDS), topic, question,
      patience: PATIENCE, state: "waiting", engaged: false, gone: false, arrivedAt: this.t,
    });
  }

  removeVisitor(visitor, happy) {
    visitor.gone = true;
    this.visitors = this.visitors.filter((item) => item !== visitor);
    this.departures.push({ id: visitor.id, kind: visitor.kind, happy, at: this.t });
    this.sfx(happy ? "coin" : "angry");
  }

  visitorGivesUp(visitor) {
    let blame = null;
    if (visitor.state === "asking") {
      if (this.t < this.stormUntil && !this.online("03")) blame = "03";
      else if (!this.online("08")) blame = "08";
    } else if (!this.online("01")) {
      blame = "01";
    }
    this.lost += 1;
    this.hurt(blame, 6);
    const why = visitor.state === "asking" ? "waited for an answer too long" : "waited in line too long";
    this.log(`A visitor ${why} and left angry.`, "bad", blame);
    this.removeVisitor(visitor, false);
  }

  async serve(visitor) {
    if (this.state !== "running" || visitor.state !== "waiting") return;
    if (this.kioskBusy) {
      this.say("owl", "One at a time!", 1.5);
      return;
    }
    if (this.t < this.jammedUntil) {
      this.say("owl", "Too many pigeons!", 2);
      this.sfx("bad");
      return;
    }
    this.kioskBusy = true;
    visitor.state = "asking";
    this.sfx("pop");
    this.speech = { text: visitor.question, state: "question" };

    try {
      await this.lag({ visitor: visitor.id });
      if (this.t < this.brokenReleaseUntil) {
        await sleep(900);
        this.emit("10", false, "No canary: v2 is live and broken", "kiosk", 6);
        this.answerFails(visitor, "Kiosk v2 bug: the Owl answers in gibberish.", "10");
        return;
      }
      this.trip = { provider: "pending", since: this.t, visitor: visitor.id };
      let first = true;
      const result = await api.ask(visitor.question, this.t < this.stormUntil, {
        onMeta: (meta) => this.onMeta(meta, visitor),
        onToken: (token) => {
          if (visitor.gone) return;
          if (first) {
            first = false;
            visitor.engaged = true;
            this.waits.push(this.t - visitor.arrivedAt);
            this.speech = { text: "", state: "answer" };
          }
          this.speech.text += token;
        },
      });
      for (const note of result.notes || []) this.noteOnce(note);
      if (visitor.gone) return;
      if (result.failed) {
        const storm = this.t < this.stormUntil;
        const blame = result.garbled ? "08" : storm ? "03" : null;
        if (result.garbled) this.emit("08", false, "Broken SSE framing: garbled answer", "kiosk");
        else if (storm) this.emit("03", false, "No fallback: the question is lost in the storm");
        this.answerFails(visitor, result.garbled ? "The answer arrived garbled."
          : "The Owl never answered.", blame);
        return;
      }
      this.askedTopics.add(visitor.topic);
      this.earn(result.provider === "parrot" ? 4 : 6, { visitor: visitor.id });
      this.rep += 2;
      this.served += 1;
      this.fx("happy", { visitor: visitor.id });
      this.removeVisitor(visitor, true);
    } finally {
      this.kioskBusy = false;
      this.trip = null;
    }
  }

  answerFails(visitor, reason, blame) {
    this.speech = { text: reason, state: "error" };
    if (visitor.gone) return;
    this.lost += 1;
    this.hurt(blame, 6);
    this.log(`${reason} The visitor left angry.`, "bad", blame);
    this.removeVisitor(visitor, false);
  }

  onMeta(meta, visitor) {
    if (meta.failed) return;
    if (meta.cost) this.earn(-meta.cost, "kiosk");
    this.trip = { ...this.trip, provider: meta.provider };
    if (meta.provider === "cache") {
      this.emit("01", true, "Cache hit: instant answer, 0 coins");
      this.fx("toss", { visitor: visitor.id });
    } else if (!this.online("01") && this.askedTopics.has(visitor.topic)) {
      this.emit("01", false, "No cache: same question, paid twice", null, 7);
    }
    if (meta.provider === "parrot") {
      this.sfx("squawk");
      this.say("parrot", "Squawk! I got this!", 2.5);
      this.emit("03", true, meta.sim_seconds < 2 ? "Circuit open: skip the Owl, ask the Parrot"
        : "Owl down: retry, then the Parrot answers");
    }
    if (meta.streamed) {
      this.emit("08", true, "Streaming: words arrive live", "kiosk", 30);
    } else if (meta.provider !== "cache") {
      this.emit("08", false, "No streaming: long silent wait", "kiosk", 30);
    }
  }

  noteOnce(note) {
    if (this.notes.has(note)) return;
    this.notes.add(note);
    const match = NOTE_SYSTEMS.find(([pattern]) => pattern.test(note));
    this.log(`Backend: ${note}.`, "warn", match ? match[1] : null);
  }

  /* Animals */

  async feed(pen) {
    if (this.state !== "running" || pen.busy) return;
    if (pen.sick > 0) {
      this.tag(pen, "too sick to eat");
      return;
    }
    pen.busy = true;
    this.sfx("pop");
    this.tag(pen, "ordering...", 30);
    try {
      await this.lag(`pen:${pen.id}`);
      const outcome = await api.feed(pen.id);
      for (const note of outcome.notes) this.noteOnce(note);
      const meals = Math.round(outcome.delivered_grams / 50);
      this.earn(-meals, `pen:${pen.id}`);
      pen.hunger += outcome.delivered_grams * HUNGER_PER_GRAM;
      pen.fedAt = this.t;
      this.fx("deliver", { pen: pen.id, attempts: outcome.attempts, meals });
      this.tag(pen, meals > 1 ? `${meals} meals!` : meals === 1 ? "yum!" : "no food?");
      if (meals > 1) {
        this.emit("04", false, `No idempotency: ${outcome.attempts} tries = ${meals} meals`,
          `pen:${pen.id}`);
        this.log(`${pen.name} got ${meals} meals for one order: the network retried ` +
          `${outcome.attempts} times and every retry was served.`, "bad", "04");
      } else if (meals === 0) {
        this.log(`${pen.name}'s order never reached the kitchen.`, "bad", "04");
      } else if (outcome.replays > 0) {
        this.emit("04", true, `Idempotency: ${outcome.attempts} tries, still 1 meal`,
          `pen:${pen.id}`);
      }
      if (pen.hunger > STUFFED_AT) {
        pen.sick = SICK_SECONDS;
        pen.hunger = 100;
        this.hurt(meals > 1 ? "04" : null, 6);
        this.sfx("bad");
        this.log(`${pen.name} ate way too much and feels sick.`, "bad", meals > 1 ? "04" : null);
      }
    } catch {
      this.tag(pen, "network down");
    } finally {
      pen.busy = false;
    }
  }

  async clean(pen) {
    if (this.state !== "running" || pen.busy || !pen.dirty || pen.cleanAt !== null) return;
    pen.busy = true;
    this.tag(pen, "cleaning...", 30);
    await this.lag(`pen:${pen.id}`);
    this.sfx("sweep");
    await sleep(1200);
    pen.dirty = false;
    pen.busy = false;
    this.fx("clean", { pen: pen.id });
    this.tag(pen, "all clean");
  }

  tag(pen, text, seconds = 2.5) {
    pen.tag = text;
    pen.tagUntil = this.t + seconds;
  }

  async approveAdoption() {
    if (this.state !== "running" || !this.adoption || this.adoption.pending) return;
    this.adoption.pending = true;
    this.sfx("pop");
    await this.lag("adoption");
    const safe = this.online("07");
    this.adoptionResult = { safe, at: this.t };
    if (safe) {
      this.earn(10, "adoption");
      this.rep += 3;
      this.emit("07", true, "Version check: one kitten, one family");
      this.log("Pixel goes home with the first family. The second one gets a polite no.", "good", "07");
    } else {
      this.hurt("07", 12);
      this.sfx("bad");
      this.emit("07", false, "Race condition: 2 families, 1 kitten");
      this.log("Both families were told yes and left with the same kitten. Tears at the office.",
        "bad", "07");
    }
    this.adoption = null;
  }

  /* Incidents */

  page(text) {
    const pager = $("#pager");
    pager.textContent = `Mika's pager: ${text}`;
    pager.hidden = false;
    this.pagerUntil = this.t + PAGER_LEAD + 2;
    this.sfx("chirp");
    this.emit("05", true, `Pager: ${text}`);
  }

  pigeons() {
    const blocked = this.online("02");
    this.pigeonsEvent = { at: this.t, blocked };
    if (blocked) {
      const admitted = this.systems["02"]?.metrics?.["pigeons admitted"] ?? "a few";
      this.earn(-1, "kiosk");
      this.sfx("honk");
      this.say("goose", "HONK! One at a time!", 3);
      this.emit("02", true, `Rate limit: ${admitted} of 500 requests pass`);
      this.log(`A pigeon swarm hits the gate. Gus throttles it: ${admitted} requests out of ` +
        "500 reach the Owl, visitors keep flowing.", "good", "02");
    } else {
      this.jammedUntil = this.t + 12;
      this.earn(-10, "kiosk");
      this.hurt("02", 4);
      this.sfx("bad");
      this.emit("02", false, "No rate limit: 500 requests jam the kiosk");
      this.log("A pigeon swarm floods the Owl with 500 requests. The kiosk is jammed and the " +
        "bill goes up by 10 coins.", "bad", "02");
    }
  }

  storm() {
    this.stormUntil = this.t + STORM_SECONDS;
    this.sfx("thunder");
    this.fx("shake", { amount: 10 });
    this.log("A storm floods the bridge to the Owl. Questions need another way through.", "warn");
  }

  raccoon() {
    const blocked = this.online("09");
    this.raccoonEvent = { at: this.t, blocked };
    if (blocked) {
      this.after(2.2, () => {
        this.earn(5, "chest");
        this.sfx("bark");
        this.say("dog", "WOOF! Wrong shelter!", 3);
        this.emit("09", true, "Badge refused: wrong tenant, access denied");
      });
      this.log("A raccoon from another shelter shows a forged badge. Rex refuses it. " +
        "Security bonus: 5 coins.", "good", "09");
    } else {
      const stolen = Math.max(0, Math.floor(this.coins * 0.3));
      this.after(4.2, () => {
        this.earn(-stolen, "chest");
        this.emit("09", false, `No auth check: the raccoon takes ${stolen} coins`);
      });
      this.hurt("09", 5);
      this.log(`A raccoon walked in with a forged badge and stole ${stolen} coins.`, "bad", "09");
    }
  }

  release() {
    const caught = this.online("10");
    this.releaseEvent = { at: this.t, caught };
    if (caught) {
      this.rep -= 1;
      this.sfx("chirp");
      this.say("canary", "v2 sounds wrong. Rollback!", 3.5);
      this.emit("10", true, "Canary release: v2 fails on 10%, rolled back");
      this.log("Kiosk v2 went to the canary first. Pip heard the errors and rolled it back.",
        "good", "10");
    } else {
      this.brokenReleaseUntil = this.t + 15;
      this.hurt("10", 3);
      this.sfx("bad");
      this.fx("shake", { amount: 6 });
      this.emit("10", false, "No canary: v2 ships to everyone and breaks");
      this.log("Kiosk v2 shipped to everyone at once. It is broken for the next 15 seconds.",
        "bad", "10");
    }
  }

  closing() {
    const waiting = this.visitors.filter((visitor) => visitor.state === "waiting");
    if (!waiting.length) return;
    if (this.online("10")) {
      this.earn(3 * waiting.length, "kiosk");
      this.served += waiting.length;
      this.emit("10", true, "Graceful shutdown: the line is drained");
      this.log(`Closing time: the kiosk drains gracefully, ${waiting.length} visitors served.`,
        "good", "10");
    } else {
      this.lost += waiting.length;
      this.hurt("10", 3 * waiting.length);
      this.emit("10", false, "Hard stop: the line is dropped");
      this.log(`Closing time: the kiosk stopped dead, ${waiting.length} visitors dropped.`,
        "bad", "10");
    }
  }

  /* Helpers */

  async lag(anchor) {
    if (this.online("06")) {
      this.emit("06", true, "Indexed query: instant", null, 25);
      return;
    }
    this.diggingUntil = this.t + DB_LAG_MS / 1000;
    this.emit("06", false, "Slow query: +1 s on every action", null, 9);
    this.fx("wait", { anchor, seconds: DB_LAG_MS / 1000 });
    await sleep(DB_LAG_MS);
  }

  /** Run something later in game time, so it respects pause and reset. */
  after(seconds, run) {
    this.timers.push({ at: this.t + seconds, run });
  }

  say(who, text, seconds) {
    this.bubbles[who] = { text, until: this.t + seconds };
  }

  hurt(systemId, rep, coins = 0) {
    this.rep -= rep;
    this.coins -= coins;
    if (systemId) this.blame[systemId] = (this.blame[systemId] || 0) + rep + coins / 3;
  }

  clock() {
    const left = Math.max(0, SHIFT_SECONDS - this.t);
    return `${Math.floor(left / 60)}:${String(Math.floor(left % 60)).padStart(2, "0")}`;
  }

  log(text, tone = "info", systemId = null) {
    const item = el("li", { "data-tone": tone }, [el("time", { text: this.clock() })]);
    if (systemId) {
      const chip = patternChip(systemId, "button");
      chip.title = "Open this station";
      chip.addEventListener("click", () => this.onOpenStation(systemId));
      item.append(chip);
    }
    item.append(el("p", { text }));
    const log = $("#log");
    log.prepend(item);
    while (log.children.length > 40) log.lastChild.remove();
  }

  /* HUD */

  renderPins() {
    const blind = !this.online("05");
    const pins = (this.incidents || []).map((incident) => el("i", {
      class: "pin",
      "data-done": String(incident.done),
      "data-blind": String(blind && !incident.done),
      style: `left:${(incident.at / SHIFT_SECONDS) * 100}%`,
      title: blind && !incident.done ? "Unknown. Build level 05 to see the forecast."
        : incident.label,
    }, [el("span", { text: blind && !incident.done ? "?" : incident.label })]));
    $("#day-pins").replaceChildren(...pins);
  }

  renderHud() {
    const blind = !this.online("05");
    const coins = $("#hud-coins");
    const value = String(Math.round(this.coins));
    if (coins.textContent !== value) {
      coins.textContent = value;
      coins.parentElement.animate([{ transform: "scale(1.18)" }, { transform: "scale(1)" }],
        { duration: 220 });
    }
    $("#hud-served").textContent = String(this.served);
    $("#hud-clock").textContent = this.clock();
    const rep = $("#hud-rep");
    rep.style.width = `${Math.max(0, Math.min(100, this.rep))}%`;
    rep.dataset.level = this.rep < 25 ? "low" : this.rep < 50 ? "mid" : "high";
    $("#day-sun").style.left = `${Math.min(100, (this.t / SHIFT_SECONDS) * 100)}%`;
    const p95 = $("#hud-p95");
    p95.parentElement.dataset.blind = String(blind);
    p95.textContent = blind ? "?" : this.waits.length
      ? `${nearestRank(this.waits.slice(-20), 95).toFixed(1)}s` : "--";
  }
}
