import { api } from "./api.js";
import { $, el, patternChip } from "./dom.js";
import { random, sleep } from "./game/helpers.js";
import { renderHud, renderPins } from "./game/hud.js";
import { closing, pigeons, raccoon, release, storm, tickIncidents } from "./game/incidents.js";
import { tag, tickAdoption, tickPens } from "./game/pens.js";
import { ADOPTIONS, ANIMALS, BEST_KEY, DAY_KEY, DB_LAG_MS, HUNGER_PER_GRAM, INCIDENTS, MAX_TASKS, SHIFT_SECONDS, SICK_SECONDS, START_COINS, START_REP, STUFFED_AT, TICK_MS } from "./game/rules.js";
import { finish, overlay, readDay, showIntro } from "./game/screens.js";
import { answerFails, noteOnce, onMeta, removeVisitor, spawnVisitor, visitorGivesUp } from "./game/visitors.js";
import { scopedKey } from "./mode.js";
import { SYSTEM_IDS, SYSTEMS } from "./systems.js";

/**
 * The rules of the shift. It owns the state, the HUD, the journal and the overlays, and
 * reports what happens through `events`, a queue the world drains to animate and play sounds.
 * A "moment" event is a pattern doing (or failing to do) its job at a place in the zoo.
 */
export class Game {
  constructor({ questions, mode, modes, onSwitchMode, onOpenStation, onMoment, onShiftStart }) {
    this.questions = Object.entries(questions);
    this.mode = mode;
    this.modes = modes;
    this.onSwitchMode = onSwitchMode;
    this.dayKey = scopedKey(DAY_KEY, mode.key);
    this.bestKey = scopedKey(BEST_KEY, mode.key);
    this.onOpenStation = onOpenStation;
    this.onMoment = onMoment;
    this.onShiftStart = onShiftStart;
    this.systems = {};
    this.state = "idle";
    this.timer = null;
    this.nextId = 1;
    $("#pause").addEventListener("click", () => this.togglePause());
    this.reset();
    showIntro(this);
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
    renderPins(this);
    if (this.state === "idle") showIntro(this);
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
    this.tasks = [];
    this.combo = 0;
    this.day = readDay(this);
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
    renderPins(this);
    renderHud(this);
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
    overlay(this, [
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
      spawnVisitor(this);
      const rush = (this.t > 120 ? 0.85 : 1) / (1 + 0.07 * (this.day - 1));
      this.nextVisitor = this.t + random(3.2, 5.4) * rush;
    }
    for (const visitor of [...this.visitors]) {
      if (visitor.engaged) continue;
      visitor.patience -= dt;
      if (visitor.patience <= 0) visitorGivesUp(this, visitor);
    }
    this.departures = this.departures.filter((departure) => this.t - departure.at < 7);
    tickPens(this, dt);
    tickIncidents(this);
    tickAdoption(this);

    this.rep = Math.min(100, this.rep);
    if (this.rep <= 0) {
      this.rep = 0;
      renderHud(this);
      finish(this, "The zoo lost the trust of its visitors", false);
      return;
    }
    if (this.t >= SHIFT_SECONDS) {
      closing(this);
      renderHud(this);
      finish(this, "Shift over", true);
      return;
    }
    renderHud(this);
  }

  /* Visitors and the Owl kiosk */

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
        answerFails(this, visitor, "Kiosk v2 bug: the Owl answers in gibberish.", "10");
        return;
      }
      this.trip = { provider: "pending", since: this.t, visitor: visitor.id };
      let first = true;
      const result = await api.ask(visitor.question, this.t < this.stormUntil, {
        onMeta: (meta) => onMeta(this, meta, visitor),
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
      for (const note of result.notes || []) noteOnce(this, note);
      if (visitor.gone) return;
      if (result.failed) {
        const storm = this.t < this.stormUntil;
        const blame = result.garbled ? "08" : storm ? "03" : null;
        if (result.garbled) this.emit("08", false, "Broken SSE framing: garbled answer", "kiosk");
        else if (storm) this.emit("03", false, "No fallback: the question is lost in the storm");
        answerFails(this, visitor, result.garbled ? "The answer arrived garbled."
          : "The Owl never answered.", blame);
        return;
      }
      this.askedTopics.add(visitor.topic);
      this.combo += 1;
      const bonus = this.comboLevel();
      const base = (result.provider === "parrot" ? 4 : 6) * (visitor.vip ? 3 : 1);
      this.earn(base + (bonus - 1) * 2, { visitor: visitor.id });
      if (bonus > 1 && this.combo % 3 === 0) this.fx("combo", { level: bonus });
      this.rep += 2;
      this.served += 1;
      this.fx("happy", { visitor: visitor.id });
      removeVisitor(this, visitor, true);
    } finally {
      this.kioskBusy = false;
      this.trip = null;
    }
  }

  /* Animals */

  async feed(pen) {
    if (this.state !== "running" || pen.busy) return;
    if (pen.sick > 0) {
      tag(this, pen, "too sick to eat");
      return;
    }
    pen.busy = true;
    this.sfx("pop");
    tag(this, pen, "ordering...", 30);
    try {
      await this.lag(`pen:${pen.id}`);
      const outcome = await api.feed(pen.id);
      for (const note of outcome.notes) noteOnce(this, note);
      const meals = Math.round(outcome.delivered_grams / 50);
      this.earn(-meals, `pen:${pen.id}`);
      pen.hunger += outcome.delivered_grams * HUNGER_PER_GRAM;
      pen.fedAt = this.t;
      this.fx("deliver", { pen: pen.id, attempts: outcome.attempts, meals });
      tag(this, pen, meals > 1 ? `${meals} meals!` : meals === 1 ? "yum!" : "no food?");
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
      tag(this, pen, "network down");
    } finally {
      pen.busy = false;
    }
  }

  async clean(pen) {
    if (this.state !== "running" || pen.busy || !pen.dirty || pen.cleanAt !== null) return;
    pen.busy = true;
    tag(this, pen, "cleaning...", 30);
    await this.lag(`pen:${pen.id}`);
    this.sfx("sweep");
    await sleep(1200);
    pen.dirty = false;
    pen.busy = false;
    this.fx("clean", { pen: pen.id });
    tag(this, pen, "all clean");
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

  /* Doing the job of a sleeping keeper by hand */

  shooPigeon() {
    const swarm = this.pigeonsEvent;
    if (this.state !== "running" || !swarm || swarm.blocked || swarm.left <= 0) return;
    swarm.left -= 1;
    this.sfx("pop");
    if (swarm.left === 0 && this.t < this.jammedUntil) {
      this.jammedUntil = this.t;
      this.earn(2, "kiosk");
      this.log("You chased the whole swarm away by hand. A rate limiter does that without you.",
        "good", "02");
    }
  }

  scareRaccoon() {
    const event = this.raccoonEvent;
    if (this.state !== "running" || !event || event.blocked || event.fledAt !== null
      || this.t - event.at > 4.2) return;
    event.scares += 1;
    this.sfx("bark");
    if (event.scares >= 3) {
      event.fledAt = this.t;
      this.earn(2, "chest");
      this.log("You scared the raccoon off yourself. An auth check stops it at the door.",
        "good", "09");
    }
  }

  rollback() {
    if (this.state !== "running" || this.t >= this.brokenReleaseUntil) return;
    this.brokenReleaseUntil = this.t;
    this.sfx("good");
    this.log("You rolled the kiosk back to v1 by hand. A canary release does it in seconds.",
      "good", "10");
  }

  /* Bao's job list */

  /** Ask Bao to walk to a place and do something there. A few jobs can wait in line. */
  enqueue(key, point, run, { valid = () => true, ready = () => true } = {}) {
    if (this.state !== "running" || this.tasks.some((task) => task.key === key)) return;
    if (this.tasks.length >= MAX_TASKS) {
      this.say("keeper", "Too many jobs!", 1.2);
      return;
    }
    this.sfx("pop");
    this.tasks.push({ key, point, run, valid, ready });
  }

  comboLevel() {
    return Math.min(4, 1 + Math.floor(this.combo / 3));
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

}
