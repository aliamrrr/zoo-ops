/**
 * The living zoo: draws the game state every frame on top of the painted scenery and turns
 * clicks into game actions. Game rules live in game.js; this file only shows them.
 */
import * as A from "./art.js";
import { Fx } from "./fx.js";
import { HUNGRY_AT, PATIENCE, SHIFT_SECONDS } from "./game.js";
import { H, LAMPS, P, PENS, SIGNS, W, paintAcorns, paintConstruction, paintGateFront,
  paintScenery } from "./scenery.js";
import { SYSTEMS, SYSTEM_IDS } from "./systems.js";

const KEEPERS = [
  { id: "01", who: "squirrel", kind: "squirrel", spot: P.squirrel, size: 54 },
  { id: "02", who: "goose", kind: "goose", spot: P.goose, size: 58 },
  { id: "03", who: "fox", kind: "fox", spot: P.fox, size: 56 },
  { id: "05", who: "meerkat", kind: "meerkat", spot: P.meerkat, size: 54, perched: true },
  { id: "06", who: "mole", kind: "mole", spot: P.mole, size: 50 },
  { id: "07", who: "beaver", kind: "beaver", spot: P.beaver, size: 54 },
  { id: "09", who: "dog", kind: "dog", spot: P.dog, size: 56 },
  { id: "10", who: "canary", kind: "canary", spot: P.nest, size: 40, perched: true },
];

/** Where the caution tape goes while a system is not built. */
const TAPES = {
  "01": [P.cache.x, P.cache.y - 4, 86],
  "02": [P.gate.x, P.gate.y - 34, 76],
  "03": [P.perch.x, P.perch.y + 54, 62],
  "04": [P.kitchen.x, P.kitchen.y - 20, 86],
  "05": [P.lookout.x, P.lookout.y - 12, 88],
  "06": [P.burrows.x, P.burrows.y + 14, 126],
  "07": [P.adoption.x, P.adoption.y - 6, 100],
  "08": [P.anthill.x, P.anthill.y - 4, 100],
  "09": [P.kennel.x, P.kennel.y - 4, 78],
  "10": [P.nestTree.x, P.nestTree.y - 26, 52],
};

const lerp = (a, b, k) => a + (b - a) * k;
const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
const between = (a, b, k) => ({ x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k) });

function moveToward(position, target, speed, dt) {
  const dx = target.x - position.x;
  const dy = target.y - position.y;
  const distance = Math.hypot(dx, dy);
  if (distance < 1) {
    position.x = target.x;
    position.y = target.y;
    return false;
  }
  const step = Math.min(distance, speed * dt);
  position.x += (dx / distance) * step;
  position.y += (dy / distance) * step;
  if (Math.abs(dx) > 0.5) position.flip = dx < 0;
  return dt > 0;
}

/** Follow a polyline of points at a 0..1 progress. */
function along(points, k) {
  const scaled = clamp(k, 0, 1) * (points.length - 1);
  const index = Math.min(points.length - 2, Math.floor(scaled));
  return between(points[index], points[index + 1], scaled - index);
}

const hop = (time, seed = 0) => Math.abs(Math.sin(time * 9 + seed)) * 5;
const blinking = (time, seed) => (time + seed * 1.7) % 3.4 < 0.13;

export class World {
  constructor(game, root, sfx) {
    this.game = game;
    this.sfx = sfx;
    this.canvas = root.querySelector("canvas");
    this.ctx = this.canvas.getContext("2d");
    this.tip = root.querySelector(".world-tip");
    this.speech = root.querySelector(".speech");
    this.background = document.createElement("canvas");
    this.scale = 1;
    this.fx = new Fx();
    this.positions = new Map();
    this.animals = Object.fromEntries(Object.entries(PENS).map(([id, pen]) => [id, {
      x: pen.x + pen.w / 2, y: pen.y + pen.h / 2 + 30, tx: 0, ty: 0, nextMove: 0, flip: false,
    }]));
    this.fox = { ...P.fox, flip: false };
    this.callouts = [];
    this.flights = [];
    this.waits = [];
    this.cheer = {};
    this.shakeSign = {};
    this.hits = [];
    this.pointer = null;
    this.hovered = null;
    this.last = performance.now();

    new ResizeObserver(() => this.resize()).observe(this.canvas);
    document.fonts?.ready.then(() => this.paintBackground());
    this.canvas.addEventListener("click", (event) => this.click(event));
    this.canvas.addEventListener("mousemove", (event) => {
      this.pointer = this.toWorld(event);
    });
    this.canvas.addEventListener("mouseleave", () => {
      this.pointer = null;
    });
    this.resize();
    requestAnimationFrame((now) => this.frame(now));
  }

  /* Canvas plumbing */

  resize() {
    const width = this.canvas.clientWidth || 960;
    // Keep the canvas light: at most 1.5x density and 1600 pixels wide.
    const ratio = Math.min(window.devicePixelRatio || 1, 1.5);
    this.scale = Math.min(width * ratio, 1600) / W;
    this.canvas.width = Math.round(W * this.scale);
    this.canvas.height = Math.round(H * this.scale);
    this.paintBackground();
  }

  paintBackground() {
    this.background.width = this.canvas.width;
    this.background.height = this.canvas.height;
    const ctx = this.background.getContext("2d");
    ctx.setTransform(this.scale, 0, 0, this.scale, 0, 0);
    paintScenery(ctx, Object.fromEntries(this.game.pens.map((pen) => [pen.id, pen.name])));
  }

  toWorld(event) {
    const box = this.canvas.getBoundingClientRect();
    return {
      x: ((event.clientX - box.left) / box.width) * W,
      y: ((event.clientY - box.top) / box.height) * H,
      cssX: event.clientX - box.left,
      cssY: event.clientY - box.top,
    };
  }

  hit(key, x, y, w, h, tip, action) {
    this.hits.push({ key, x, y, w, h, tip, action });
  }

  target(point) {
    if (!point) return null;
    for (let i = this.hits.length - 1; i >= 0; i -= 1) {
      const hit = this.hits[i];
      if (point.x >= hit.x && point.x <= hit.x + hit.w && point.y >= hit.y
        && point.y <= hit.y + hit.h) return hit;
    }
    return null;
  }

  click(event) {
    this.sfx.unlock();
    this.target(this.toWorld(event))?.action?.();
  }

  /* Events coming from the game */

  anchor(anchor, id) {
    if (anchor && typeof anchor === "object") {
      const position = this.positions.get(anchor.visitor) || P.serve;
      return { x: position.x, y: position.y - 62 };
    }
    if (typeof anchor === "string") {
      if (anchor.startsWith("pen:")) {
        const pen = PENS[anchor.slice(4)];
        return { x: pen.x + pen.w / 2, y: pen.y - 26 };
      }
      if (anchor === "kiosk") return { x: P.owl.x, y: 352 };
      if (anchor === "chest") return { x: P.chest.x, y: P.chest.y - 48 };
      if (anchor === "adoption") return { x: P.adoption.x, y: P.adoption.y - 112 };
    }
    const sign = SIGNS[id];
    return { x: sign.x + (sign.dx || 0), y: sign.y + (sign.below ? 16 : -16), below: sign.below };
  }

  handle(event, time) {
    switch (event.type) {
      case "moment": {
        const point = this.anchor(event.anchor, event.id);
        for (const other of this.callouts) {
          if (Math.abs(other.x - point.x) < 200 && Math.abs(other.y - point.y) < 40) other.slot += 1;
        }
        this.callouts.push({ ...event, ...point, slot: 0, born: time });
        if (event.good) {
          this.cheer[event.id] = time + 1.4;
          this.fx.burst("spark", point.x, point.y - 8, 7, SYSTEMS[event.id].color);
          this.sfx.play("good");
        } else {
          this.shakeSign[event.id] = time + 0.7;
          this.fx.burst("puff", point.x, point.y - 4, 5, "rgba(229,72,77,0.5)");
          this.sfx.play("bad");
        }
        break;
      }
      case "coins": {
        const point = this.anchor(event.anchor, "01");
        const gain = event.amount > 0;
        this.fx.pop(`${gain ? "+" : ""}${event.amount}`, point.x, point.y + 10,
          gain ? "#ffd23f" : "#ff8a8a", gain ? 24 : 20);
        if (gain) this.fx.burst("coin", point.x, point.y + 20, Math.min(8, event.amount));
        break;
      }
      case "happy": {
        const position = this.positions.get(event.visitor);
        if (position) this.fx.burst("heart", position.x, position.y - 50, 6);
        break;
      }
      case "toss": {
        const to = this.positions.get(event.visitor) || P.serve;
        this.flights.push({ icon: "acorn", from: { x: P.cache.x, y: P.cache.y - 60 },
          to: { x: to.x, y: to.y - 40 }, start: time, duration: 0.5, arc: 70,
          land: () => this.fx.burst("spark", to.x, to.y - 44, 8, "#ffd23f") });
        break;
      }
      case "deliver":
        this.deliver(event, time);
        break;
      case "clean": {
        const pen = PENS[event.pen];
        this.fx.burst("spark", pen.x + pen.w / 2, pen.y + pen.h / 2 + 20, 12, "#ffffff");
        this.sfx.play("good");
        break;
      }
      case "wait":
        this.waits.push({ ...this.anchor(event.anchor, "06"), start: time, seconds: event.seconds });
        break;
      case "shake":
        this.fx.shake = event.amount;
        break;
      case "confetti":
        for (const x of [240, 520, 760, 1040]) this.fx.burst("confetti", x, 420, 26);
        break;
      case "sfx":
        this.sfx.play(event.name);
        break;
      default:
    }
  }

  /** One order: tickets fly to the kitchen (one per network try), bowls fly back. */
  deliver(event, time) {
    const animal = this.animals[event.pen];
    const kitchen = { x: P.kitchen.x, y: P.kitchen.y - 56 };
    const mouth = { x: animal.x, y: animal.y - 40 };
    for (let i = 0; i < event.attempts; i += 1) {
      this.flights.push({ icon: "ticket", from: mouth, to: kitchen, start: time + i * 0.2,
        duration: 0.4, arc: 40 });
    }
    const cooked = time + event.attempts * 0.2 + 0.35;
    for (let i = 0; i < event.meals; i += 1) {
      this.flights.push({ icon: "bowl", from: kitchen, to: mouth, start: cooked + i * 0.28,
        duration: 0.5, arc: 60, land: () => {
          this.fx.burst("crumb", mouth.x, mouth.y + 14, 6, "#c98e52");
          this.fx.burst("heart", mouth.x, mouth.y - 20, i === 0 ? 3 : 0);
          this.sfx.play("munch");
          if (i > 0) this.fx.pop(`x${i + 1}!`, mouth.x + 26, mouth.y - 34, "#ff8a8a", 22);
        } });
    }
    if (event.meals === 1 && event.attempts > 1) {
      this.flights.push({ icon: "none", from: kitchen, to: kitchen, start: cooked, duration: 0.1,
        arc: 0, land: () => this.fx.pop(`${event.attempts - 1} retry ignored`, kitchen.x,
          kitchen.y - 40, "#9be28a", 16) });
    }
  }

  /* Frame */

  frame(now) {
    requestAnimationFrame((next) => this.frame(next));
    // 30 frames per second is plenty here, and nothing is drawn while the zoo is not visible.
    if (now - this.last < 1000 / 31 || document.hidden || this.canvas.offsetParent === null) return;
    const dt = Math.min(0.05, (now - this.last) / 1000);
    this.last = now;
    const time = now / 1000;
    const game = this.game;
    const move = game.state === "running" ? dt : 0;
    const ctx = this.ctx;

    for (const event of game.events.splice(0)) this.handle(event, time);
    this.fx.update(dt);
    const [shakeX, shakeY] = this.fx.offset();

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.drawImage(this.background, 0, 0);
    ctx.setTransform(this.scale, 0, 0, this.scale, shakeX * this.scale, shakeY * this.scale);
    ctx.lineJoin = "round";
    this.hits = [];

    this.drawWater(ctx, time);
    this.drawGroundThings(ctx, time);
    const actors = [];
    this.addKeepers(actors, ctx, time, move);
    this.addOwl(actors, ctx, time);
    this.addPens(actors, ctx, time, move);
    this.addVisitors(actors, ctx, time, move);
    this.addAdoption(actors, ctx, time);
    this.addRaccoon(actors, ctx, time);
    actors.sort((a, b) => a.y - b.y);
    for (const actor of actors) actor.draw();
    const small = (hit) => (hit.key.startsWith("dirt") ? 1 : 0);
    this.hits.sort((a, b) => small(a) - small(b));

    paintGateFront(ctx, time);
    this.drawFlyers(ctx, time);
    this.fx.draw(ctx);
    this.drawWeather(ctx, time);
    this.drawLight(ctx, time);
    this.drawSigns(ctx, time);
    this.drawWaits(ctx, time);
    this.drawCallouts(ctx, time);
    if (game.state !== "running") this.hits = [];
    this.drawHover(ctx, time);
    this.syncSpeech();
  }

  /* Ground level */

  drawWater(ctx, time) {
    ctx.lineCap = "round";
    for (let i = 0; i < 9; i += 1) {
      const angle = i * 2.4 + 0.6;
      const radius = 0.55 + ((i * 37) % 40) / 100;
      const x = 640 + Math.cos(angle) * 190 * radius;
      const y = 276 + Math.sin(angle) * 100 * radius;
      if (Math.hypot((x - 640) / 96, (y - 258) / 58) < 1) continue;
      const wave = Math.sin(time * 1.6 + i * 1.3);
      ctx.globalAlpha = 0.35 + wave * 0.25;
      A.line(ctx, [x - 9 - wave * 3, y, x + 9 + wave * 3, y], "#ffffff", 2.5);
    }
    ctx.globalAlpha = 1;
    if (this.game.t < this.game.stormUntil) {
      const swell = Math.sin(time * 3) * 3;
      A.rrect(ctx, 606, 318 + swell, 68, 78, 14, "rgba(70,150,220,0.72)");
      for (let i = 0; i < 3; i += 1) {
        A.line(ctx, [614, 334 + i * 22 + swell, 628, 330 + i * 22 + swell, 642, 334 + i * 22 + swell,
          656, 330 + i * 22 + swell, 668, 334 + i * 22 + swell], "rgba(255,255,255,0.8)", 2.5);
      }
    }
  }

  drawGroundThings(ctx, time) {
    const game = this.game;
    if (game.online("01")) paintAcorns(ctx, game.askedTopics.size);
    for (const id of SYSTEM_IDS) {
      if (game.online(id) || !Object.keys(game.systems).length) continue;
      const [x, y, width] = TAPES[id];
      paintConstruction(ctx, x, y, width);
      A.cone(ctx, x + width / 2 + 14, y + 12, 13);
    }

    // The version plate of the kiosk (deploys)
    const release = game.releaseEvent;
    const broken = game.t < game.brokenReleaseUntil;
    const trial = release && release.caught && game.t - release.at > 1.4 && game.t - release.at < 3.4;
    const label = broken ? "v2" : trial ? "v2 10%" : "v1";
    const plate = broken ? (Math.floor(time * 4) % 2 ? "#ff8a8a" : "#e5484d") : trial ? "#ffd23f" : "#c9f2bd";
    A.rrect(ctx, 573 - 24, 270, 48, 18, 9, plate, A.OUTLINE, 2);
    A.text(ctx, label, 573, 280, { size: 11, weight: 800 });

    // Ants at work around their hill
    if (game.online("08")) {
      for (let i = 0; i < 5; i += 1) {
        const angle = time * 0.9 + i * 1.26;
        this.ant(ctx, P.anthill.x + Math.cos(angle) * 52, P.anthill.y + 4 + Math.sin(angle) * 9, 1);
      }
    }
    for (const pen of game.pens) {
      if (!pen.dirty || !pen.dirtSpot) continue;
      const box = PENS[pen.id];
      const x = box.x + pen.dirtSpot.x * box.w;
      const y = box.y + pen.dirtSpot.y * box.h;
      A.oval(ctx, x - 7, y + 2, 9, 6, "#8f6040", A.OUTLINE, 2);
      A.oval(ctx, x + 7, y + 3, 8, 5, "#8f6040", A.OUTLINE, 2);
      A.oval(ctx, x, y - 4, 9, 7, "#a9744a", A.OUTLINE, 2);
      for (const dx of [-8, 0, 8]) {
        const wobble = Math.sin(time * 3 + dx) * 2;
        A.line(ctx, [x + dx, y - 16, x + dx + wobble, y - 22, x + dx - wobble, y - 28],
          "rgba(120,150,70,0.8)", 2);
      }
      if (pen.antsSince !== null) {
        const progress = clamp((game.t - pen.antsSince) / 2.6, 0, 1);
        const start = { x: P.anthill.x + 30, y: P.anthill.y - 6 };
        for (let i = 0; i < 16; i += 1) {
          const k = (i / 16 + time * 0.22) % 1;
          if (k > progress) continue;
          const point = between(start, { x, y }, k);
          this.ant(ctx, point.x, point.y + Math.sin(k * 40) * 2, 1);
        }
      } else {
        this.hit(`dirt:${pen.id}`, x - 20, y - 26, 40, 40, `Clean ${pen.name}'s pen`,
          () => game.clean(pen));
      }
    }
  }

  ant(ctx, x, y, s) {
    A.oval(ctx, x - 3 * s, y, 2.2 * s, 1.8 * s, "#6e2f2b");
    A.oval(ctx, x, y, 1.8 * s, 1.5 * s, "#6e2f2b");
    A.oval(ctx, x + 3 * s, y, 2 * s, 1.7 * s, "#6e2f2b");
  }

  /* Actors */

  addKeepers(actors, ctx, time, move) {
    const game = this.game;
    const known = Object.keys(game.systems).length > 0;
    KEEPERS.forEach((keeper, index) => {
      const built = game.online(keeper.id);
      const said = game.bubbles[keeper.who];
      const talking = said && said.until > game.t;
      const cheering = this.cheer[keeper.id] > time;
      let { x, y } = keeper.spot;
      const options = { time, shadow: !keeper.perched };

      if (keeper.who === "fox") {
        this.stepFox(move);
        ({ x, y } = this.fox);
        options.flip = this.fox.flip;
        if (this.fox.moving) options.lift = hop(time);
        if (this.fox.carrying) {
          options.carry = (c, u) => A.envelope(c, 0.27 * u, -0.3 * u, 0.13 * u);
        }
      }
      if (keeper.who === "canary" && this.canaryFlying()) return;
      if (keeper.who === "mole" && game.t < game.diggingUntil) {
        options.squash = Math.sin(time * 26) * 0.06;
        if (Math.random() < 0.3) this.fx.burst("dirt", x + (Math.random() - 0.5) * 50, y - 6, 1);
      }
      if (keeper.who === "dog" && game.raccoonEvent?.blocked) {
        const age = game.t - game.raccoonEvent.at;
        if (age > 1.8 && age < 5) {
          options.eyes = "angry";
          options.lift = hop(time, 1);
          x += clamp((age - 2.4) * 34, 0, 46);
        }
      }
      if (keeper.who === "goose" && game.pigeonsEvent?.blocked
        && game.t - game.pigeonsEvent.at < 4.5) {
        options.eyes = "angry";
        options.flap = (Math.sin(time * 20) + 1) / 2;
        options.lift = hop(time, 2);
      }
      if (keeper.who === "meerkat" && game.t < game.pagerUntil) options.lift = hop(time, 3) * 0.6;

      if (!built && known) options.eyes = "asleep";
      else if (!options.eyes) {
        options.eyes = talking || cheering ? "happy" : blinking(time, index) ? "blink" : "open";
      }
      if (cheering && built) options.lift = Math.max(options.lift || 0, hop(time, index));
      if (options.squash === undefined) {
        options.squash = Math.sin(time * (built ? 2.4 : 1.2) + index) * (built ? 0.025 : 0.015);
      }
      actors.push({ y, draw: () => {
        A.drawCritter(ctx, keeper.kind, x, y, keeper.size, options);
        if (!built && known) A.zzz(ctx, x + keeper.size * 0.28, y - keeper.size * 0.95, time + index, 15);
        if (talking) A.bubble(ctx, said.text, x, y - keeper.size - 6, { size: 14 });
      } });
    });

    const parrot = game.bubbles.parrot;
    const squawking = parrot && parrot.until > game.t;
    actors.push({ y: P.perch.y + 60, draw: () => {
      A.drawCritter(ctx, "parrot", P.perch.x, P.perch.y, 50, { time, shadow: false,
        eyes: squawking ? "happy" : blinking(time, 9) ? "blink" : "open",
        lift: squawking ? hop(time) : 0, flap: squawking ? (Math.sin(time * 18) + 1) / 2 : 0 });
      if (squawking) A.bubble(ctx, parrot.text, P.perch.x, P.perch.y - 60, { size: 14 });
    } });
  }

  stepFox(move) {
    const game = this.game;
    const trip = game.trip;
    let target = P.fox;
    this.fox.carrying = false;
    if (game.online("03") && trip && trip.provider !== "cache" && game.t - trip.since > 0.12) {
      this.fox.carrying = true;
      const storm = game.t < game.stormUntil;
      if (trip.provider === "parrot") target = P.perchFoot;
      else if (storm) target = game.t - trip.since < 1.3 ? P.bridgeFoot : P.perchFoot;
      else target = P.bridgeTop;
    }
    this.fox.moving = moveToward(this.fox, target, 300, move);
    if (!this.fox.moving && target === P.fox) this.fox.flip = true;
  }

  addOwl(actors, ctx, time) {
    const game = this.game;
    const dizzy = game.t < game.jammedUntil || game.t < game.brokenReleaseUntil;
    const thinking = game.kioskBusy && game.speech.state === "question";
    const said = game.bubbles.owl;
    const options = { time,
      eyes: dizzy ? "sick" : game.speech.state === "answer" && game.kioskBusy ? "happy"
        : blinking(time, 4) ? "blink" : "open",
      squash: thinking ? Math.sin(time * 9) * 0.035 : Math.sin(time * 2) * 0.02,
      flap: thinking ? (Math.sin(time * 9) + 1) / 5 : 0 };
    actors.push({ y: P.owl.y, draw: () => {
      A.drawCritter(ctx, "owl", P.owl.x, P.owl.y, 92, options);
      if (game.t < game.brokenReleaseUntil && Math.random() < 0.25) {
        this.fx.burst("spark", P.owl.x + (Math.random() - 0.5) * 70, P.owl.y - 60, 1, "#ff8a8a");
      }
      if (said && said.until > game.t && !game.speech.text) {
        A.bubble(ctx, said.text, P.owl.x, P.owl.y - 98, { size: 15 });
      }
    } });

    // An unescorted letter when the fox is not on duty
    const trip = game.trip;
    if (trip && !game.online("03") && trip.provider !== "cache") {
      const age = game.t - trip.since;
      const storm = game.t < game.stormUntil;
      const route = [{ x: P.serve.x, y: P.serve.y - 40 }, P.bridgeFoot, P.bridgeTop];
      if (storm && age > 0.55) {
        if (!trip.splashed) {
          trip.splashed = true;
          this.fx.burst("splash", 640, 356, 12);
          this.sfx.play("splash");
        }
      } else if (age < 0.9) {
        const point = along(route, age / 0.9);
        actors.push({ y: 720, draw: () => A.envelope(ctx, point.x, point.y - 8 - Math.sin(age * 12) * 3, 10) });
      }
    }
  }

  addPens(actors, ctx, time, move) {
    const game = this.game;
    const blind = !game.online("05");
    game.pens.forEach((pen, index) => {
      const box = PENS[pen.id];
      const animal = this.animals[pen.id];
      const hungry = pen.hunger < HUNGRY_AT;
      const sick = pen.sick > 0;
      const fed = game.t - pen.fedAt < 2.6;
      if (time > animal.nextMove) {
        animal.tx = box.x + 44 + Math.random() * (box.w - 88);
        animal.ty = box.y + 100 + Math.random() * (box.h - 126);
        animal.nextMove = time + 2.5 + Math.random() * 3.5;
      }
      const walking = !sick && moveToward(animal, { x: animal.tx, y: animal.ty }, hungry ? 9 : 22, move);
      const options = { time, flip: animal.flip,
        eyes: sick ? "sick" : hungry ? "sad" : fed ? "happy" : blinking(time, index + 5) ? "blink" : "open",
        lift: fed ? hop(time, index) : walking ? hop(time * 0.7, index) * 0.5 : 0,
        squash: hungry ? Math.sin(time * 16) * 0.03 : Math.sin(time * 2.2 + index) * 0.02 };
      const tagged = pen.tag && game.t < pen.tagUntil;

      actors.push({ y: animal.y, draw: () => {
        A.drawCritter(ctx, pen.kind, animal.x, animal.y, 72, options);
        if (tagged) {
          A.bubble(ctx, pen.tag, animal.x, animal.y - 78, { size: 13 });
        } else if (hungry && !sick) {
          const by = animal.y - 96 + Math.sin(time * 4) * 2;
          A.oval(ctx, animal.x + 22, by, 17, 15, "#ffffff", A.OUTLINE, 2);
          A.oval(ctx, animal.x + 10, by + 17, 4, 4, "#ffffff", A.OUTLINE, 2);
          A.bowl(ctx, animal.x + 22, by + 3, 9, false);
        }
      } });

      const barX = box.x + box.w / 2 - 38;
      const barY = box.y + 14;
      A.rrect(ctx, barX, barY, 76, 11, 5.5, "rgba(75,55,87,0.85)");
      if (blind) {
        A.text(ctx, "?  ?  ?", barX + 38, barY + 6, { size: 10, color: "#cfc6da", weight: 800 });
      } else {
        const level = clamp(pen.hunger / 100, 0, 1);
        const color = pen.hunger < HUNGRY_AT ? "#ff6b6b" : pen.hunger > 100 ? "#ffb347" : "#7fe07a";
        if (level > 0.03) A.rrect(ctx, barX + 2, barY + 2, 72 * level, 7, 3.5, color);
      }
      const tip = sick ? `${pen.name} is too sick to eat` : pen.busy ? `${pen.name}: order on its way`
        : `Feed ${pen.name}`;
      this.hit(`pen:${pen.id}`, box.x, box.y, box.w, box.h, tip, () => game.feed(pen));
    });
  }

  addVisitors(actors, ctx, time, move) {
    const game = this.game;
    const blind = !game.online("05");
    const waiting = game.visitors.filter((visitor) => visitor.state === "waiting");
    const seen = new Set();

    for (const visitor of game.visitors) {
      seen.add(visitor.id);
      if (!this.positions.has(visitor.id)) this.positions.set(visitor.id, { ...P.spawn, flip: false });
      const position = this.positions.get(visitor.id);
      const slot = visitor.state === "asking" ? P.serve : P.queue[waiting.indexOf(visitor)] || P.queue[5];
      let walking;
      if (!position.entered) {
        walking = moveToward(position, P.entry, 150, move);
        if (!walking && move) position.entered = true;
      } else {
        walking = moveToward(position, slot, 150, move);
      }
      const upset = visitor.state === "waiting" && visitor.patience < 8;
      const front = waiting[0] === visitor;
      const options = { time, flip: walking ? position.flip : false,
        eyes: upset ? "angry" : blinking(time, visitor.id) ? "blink" : "open",
        lift: walking ? hop(time, visitor.id) : 0,
        squash: upset ? Math.sin(time * 18) * 0.03 : Math.sin(time * 2.5 + visitor.id) * 0.02 };

      actors.push({ y: position.y, draw: () => {
        A.drawCritter(ctx, visitor.kind, position.x, position.y, 46, options);
        if (visitor.state !== "waiting") return;
        const top = position.y - 62;
        if (!blind) {
          const k = clamp(visitor.patience / PATIENCE, 0, 1);
          A.rrect(ctx, position.x - 19, top, 38, 9, 4.5, "rgba(75,55,87,0.85)");
          if (k > 0.05) {
            A.rrect(ctx, position.x - 17, top + 2, 34 * k, 5, 2.5,
              k < 0.3 ? "#ff6b6b" : k < 0.6 ? "#ffb347" : "#7fe07a");
          }
        }
        if (upset) A.anger(ctx, position.x + 17, top - 6, 5);
        if (front && !walking && !game.kioskBusy && game.t < 30) {
          const bounce = Math.sin(time * 6) * 4;
          A.poly(ctx, [position.x - 9, top - 26 + bounce, position.x + 9, top - 26 + bounce,
            position.x, top - 12 + bounce], "#ffd23f", A.OUTLINE, 2.5);
          A.text(ctx, "click me!", position.x, top - 38 + bounce,
            { size: 14, color: "#ffffff", stroke: A.OUTLINE, weight: 800 });
        }
      } });
      if (visitor.state === "waiting") {
        this.hit(`visitor:${visitor.id}`, position.x - 22, position.y - 60, 44, 64,
          `"${visitor.question}" Click to ask the Owl.`, () => game.serve(visitor));
      }
    }

    for (const departure of game.departures) {
      seen.add(departure.id);
      const position = this.positions.get(departure.id) || { ...P.serve, flip: false };
      this.positions.set(departure.id, position);
      if (departure.happy) {
        if (position.y < 505 && !position.leaving) moveToward(position, { x: 640, y: 506 }, 170, move);
        else {
          position.leaving = true;
          moveToward(position, P.exit, 170, move);
        }
      } else if (position.x > 160 && !position.leaving) {
        moveToward(position, { x: 156, y: position.entered ? 494 : position.y }, 170, move);
      } else {
        position.leaving = true;
        moveToward(position, P.spawn, 170, move);
      }
      actors.push({ y: position.y, draw: () => {
        A.drawCritter(ctx, departure.kind, position.x, position.y, 46, { time, flip: position.flip,
          eyes: departure.happy ? "happy" : "angry", lift: hop(time, departure.id) });
        if (departure.happy) A.heart(ctx, position.x + 16, position.y - 58 + Math.sin(time * 5) * 2, 6);
        else A.anger(ctx, position.x + 16, position.y - 56, 5);
      } });
    }
    for (const id of this.positions.keys()) if (!seen.has(id)) this.positions.delete(id);
  }

  addAdoption(actors, ctx, time) {
    const game = this.game;
    const [a, b] = P.families;
    const cottage = P.adoption;
    if (game.adoption) {
      const left = clamp((game.adoption.deadline - game.t) / (game.adoption.deadline - game.adoption.since), 0, 1);
      actors.push({ y: a.y, draw: () => {
        A.drawCritter(ctx, "rabbit", a.x, a.y, 44, { time, lift: hop(time * 0.6, 1) * 0.6, eyes: "happy" });
        A.drawCritter(ctx, "frog", b.x, b.y, 42, { time, flip: true, lift: hop(time * 0.6, 2) * 0.6, eyes: "happy" });
        A.drawCritter(ctx, "cat", (a.x + b.x) / 2, a.y - 26, 30, { time, eyes: blinking(time, 2) ? "blink" : "open" });
        A.heart(ctx, (a.x + b.x) / 2, a.y - 66 + Math.sin(time * 4) * 3, 7);
        A.bubble(ctx, "Adopt Pixel?", cottage.x, cottage.y - 122 + Math.sin(time * 5) * 2, { size: 14 });
        A.rrect(ctx, cottage.x - 36, cottage.y - 116, 72, 9, 4.5, "rgba(75,55,87,0.85)");
        A.rrect(ctx, cottage.x - 34, cottage.y - 114, 68 * left, 5, 2.5, left < 0.3 ? "#ff6b6b" : "#ffb347");
      } });
      this.hit("adoption", cottage.x - 100, cottage.y - 110, 170, 150, "Approve the adoption",
        () => game.approveAdoption());
    } else if (game.adoptionResult && game.t - game.adoptionResult.at < 4.5) {
      const k = (game.t - game.adoptionResult.at) / 4.5;
      const safe = game.adoptionResult.safe;
      const ax = a.x - k * 190;
      const bx = b.x + (safe ? 0 : -k * 150);
      actors.push({ y: a.y, draw: () => {
        A.drawCritter(ctx, "rabbit", ax, a.y, 44, { time, flip: true, lift: hop(time, 1), eyes: "happy" });
        A.drawCritter(ctx, "cat", ax + 26, a.y, 28, { time, flip: true, lift: hop(time, 4), eyes: "happy" });
        A.heart(ctx, ax, a.y - 58, 6);
        A.drawCritter(ctx, "frog", bx, b.y, 42, { time, flip: true, lift: safe ? 0 : hop(time, 2),
          eyes: safe ? "blink" : "happy" });
        if (!safe) {
          ctx.globalAlpha = 0.55 + Math.sin(time * 16) * 0.3;
          A.drawCritter(ctx, "cat", bx + 26, b.y, 28, { time, flip: true, lift: hop(time, 5) });
          ctx.globalAlpha = 1;
          A.bubble(ctx, "Two Pixels?!", bx + 14, b.y - 52, { size: 13 });
        } else if (k < 0.6) {
          A.bubble(ctx, "Next time!", bx, b.y - 48, { size: 13 });
        }
      } });
    }
  }

  addRaccoon(actors, ctx, time) {
    const event = this.game.raccoonEvent;
    if (!event) return;
    const age = this.game.t - event.at;
    const lurk = { x: 836, y: 700 };
    const chest = { x: P.chest.x + 40, y: P.chest.y + 12 };
    let point;
    let options = { time, flip: true, lift: hop(time * 0.8) * 0.6 };
    let loot = false;
    if (event.blocked) {
      if (age > 5) return;
      if (age < 2.2) point = between(P.staffDoor, lurk, age / 2.2);
      else if (age < 2.7) {
        point = lurk;
        options = { time, flip: true, lift: 12, eyes: "sad" };
      } else {
        point = between(lurk, { x: 960, y: 790 }, (age - 2.7) / 1.4);
        options = { time, flip: false, lift: hop(time * 1.6), eyes: "sad" };
      }
    } else {
      if (age > 8.4) return;
      if (age < 4.2) point = along([P.staffDoor, lurk, chest], age / 4.2);
      else if (age < 5) {
        point = chest;
        options.eyes = "happy";
      } else {
        point = along([chest, lurk, P.staffDoor], (age - 5) / 3.2);
        options = { time, flip: false, lift: hop(time), eyes: "happy" };
        loot = true;
      }
    }
    actors.push({ y: point.y, draw: () => {
      if (loot) {
        A.oval(ctx, point.x - 20, point.y - 34, 14, 15, "#e2b98a", A.OUTLINE, 2.5);
        A.coin(ctx, point.x - 20, point.y - 34, 6);
      }
      A.drawCritter(ctx, "raccoon", point.x, point.y, 52, options);
      if (event.blocked && age > 2.2 && age < 2.9) A.bubble(ctx, "!", point.x, point.y - 62, { size: 16 });
    } });
  }

  /* Things in the air */

  canaryFlying() {
    const event = this.game.releaseEvent;
    return event && event.caught && this.game.t - event.at < 4.8;
  }

  drawFlyers(ctx, time) {
    const game = this.game;
    const flap = (seed) => (Math.sin(time * 20 + seed) + 1) / 2;

    const pigeons = game.pigeonsEvent;
    if (pigeons) {
      const age = game.t - pigeons.at;
      const limit = pigeons.blocked ? 4.6 : 15;
      for (let i = 0; i < 10 && age < limit; i += 1) {
        const wobble = { x: Math.sin(time * 5 + i * 2) * 6, y: Math.cos(time * 6 + i) * 5 };
        let point;
        if (pigeons.blocked) {
          const hover = { x: 110 + (i % 5) * 20, y: 668 + Math.floor(i / 5) * 22 };
          point = age < 1.3 ? between({ x: hover.x - 60, y: 800 }, hover, age / 1.3)
            : age < 2.4 ? hover
              : between(hover, { x: hover.x - 200, y: 820 }, (age - 2.4) / 2.2);
        } else {
          const orbit = time * 2.2 + i * 0.63;
          const around = { x: P.owl.x + Math.cos(orbit) * 74, y: P.owl.y - 60 + Math.sin(orbit) * 30 };
          point = age < 2.6 ? along([{ x: 150, y: 790 }, { x: 170, y: 520 }, { x: 400, y: 380 }, around], age / 2.6)
            : age < 12 ? around
              : between(around, { x: around.x + 500, y: -80 }, (age - 12) / 3);
        }
        A.drawCritter(ctx, "pigeon", point.x + wobble.x, point.y + wobble.y, 34,
          { time, shadow: false, flap: flap(i), flip: i % 2 === 0, eyes: pigeons.blocked && age > 1.3 ? "sad" : "open" });
      }
    }

    const release = game.releaseEvent;
    if (release) {
      const age = game.t - release.at;
      const kiosk = { x: P.owl.x - 50, y: P.owl.y - 96 };
      if (release.caught && age < 4.8) {
        const point = age < 1.4 ? between(P.nest, kiosk, age / 1.4)
          : age < 3.4 ? { x: kiosk.x + Math.sin(time * 3) * 6, y: kiosk.y + Math.cos(time * 4) * 4 }
            : between(kiosk, P.nest, (age - 3.4) / 1.4);
        A.parcel(ctx, point.x, point.y + 6, 11, "v2", age > 2.2);
        A.drawCritter(ctx, "canary", point.x, point.y, 38, { time, shadow: false, flap: flap(3),
          flip: age > 3.4, eyes: age > 2.2 && age < 3.4 ? "angry" : "open" });
      } else if (!release.caught && age < 0.7) {
        const y = lerp(-30, P.owl.y - 110, age / 0.7);
        A.parcel(ctx, P.owl.x, y, 14, "v2", true);
      }
    }

    this.flights = this.flights.filter((flight) => {
      const k = (time - flight.start) / flight.duration;
      if (k < 0) return true;
      if (k >= 1) {
        flight.land?.();
        return false;
      }
      const point = between(flight.from, flight.to, k);
      const y = point.y - Math.sin(k * Math.PI) * flight.arc;
      if (flight.icon === "bowl") A.bowl(ctx, point.x, y, 12);
      else if (flight.icon === "acorn") A.acorn(ctx, point.x, y, 11);
      else if (flight.icon === "ticket") {
        A.rrect(ctx, point.x - 8, y - 10, 16, 20, 3, "#fffdf5", A.OUTLINE, 2);
        A.line(ctx, [point.x - 4, y - 4, point.x + 4, y - 4], A.OUTLINE, 1.5);
        A.line(ctx, [point.x - 4, y + 1, point.x + 4, y + 1], A.OUTLINE, 1.5);
      }
      return true;
    });

    const day = clamp(game.t / SHIFT_SECONDS, 0, 1);
    if (day < 0.62 && game.t >= game.stormUntil) {
      for (let i = 0; i < 3; i += 1) {
        const x = 260 + i * 330 + Math.sin(time * 0.5 + i * 2) * 120;
        const y = 500 - i * 130 + Math.sin(time * 0.8 + i) * 60;
        const wing = Math.abs(Math.sin(time * 14 + i)) * 6 + 1.5;
        const color = ["#ff8fab", "#8f7ae6", "#ffd23f"][i];
        A.oval(ctx, x - wing * 0.7, y, wing, 5, color, A.OUTLINE, 1.2, -0.4);
        A.oval(ctx, x + wing * 0.7, y, wing, 5, color, A.OUTLINE, 1.2, 0.4);
        A.oval(ctx, x, y, 1.4, 4, A.OUTLINE);
      }
    }
  }

  /* Sky */

  drawWeather(ctx, time) {
    const game = this.game;
    if (game.t >= game.stormUntil) return;
    const haze = ctx.createRadialGradient(640, 270, 60, 640, 270, 400);
    haze.addColorStop(0, "rgba(46,52,90,0.42)");
    haze.addColorStop(1, "rgba(46,52,90,0)");
    ctx.fillStyle = haze;
    ctx.fillRect(0, 0, W, H);
    ctx.lineCap = "round";
    for (let i = 0; i < 70; i += 1) {
      const x = 380 + ((i * 53) % 520);
      const y = 130 + ((i * 97 + time * 520) % 330);
      A.line(ctx, [x, y, x - 5, y + 15], "rgba(200,232,255,0.8)", 2);
    }
    for (let i = 0; i < 4; i += 1) {
      const x = 470 + i * 110 + Math.sin(time * 0.7 + i) * 24;
      const y = 128 + (i % 2) * 18;
      for (const [dx, dy, r] of [[-26, 6, 20], [0, -6, 27], [28, 6, 21], [2, 12, 24]]) {
        A.oval(ctx, x + dx, y + dy, r + 2.5, r * 0.8 + 2.5, "#4b4f72");
      }
      for (const [dx, dy, r] of [[-26, 6, 20], [0, -6, 27], [28, 6, 21], [2, 12, 24]]) {
        A.oval(ctx, x + dx, y + dy, r, r * 0.8, "#7a80a8");
      }
    }
    if (Math.sin(time * 1.7) > 0.985) {
      ctx.fillStyle = "rgba(255,255,255,0.4)";
      ctx.fillRect(0, 0, W, H);
      A.poly(ctx, [600, 150, 628, 150, 612, 200, 634, 200, 588, 268, 602, 214, 584, 214], "#fff6a8",
        A.OUTLINE, 2.5);
    }
  }

  drawLight(ctx, time) {
    const day = clamp(this.game.t / SHIFT_SECONDS, 0, 1);
    if (day < 0.12) {
      ctx.fillStyle = `rgba(255,214,140,${0.14 * (1 - day / 0.12)})`;
      ctx.fillRect(0, 0, W, H);
      return;
    }
    if (day < 0.62) return;
    const dusk = (day - 0.62) / 0.38;
    ctx.globalCompositeOperation = "multiply";
    ctx.fillStyle = `rgb(${255 - 96 * dusk},${255 - 112 * dusk},${255 - 44 * dusk})`;
    ctx.fillRect(0, 0, W, H);
    ctx.globalCompositeOperation = "source-over";
    ctx.fillStyle = `rgba(255,130,90,${0.16 * Math.sin(dusk * Math.PI)})`;
    ctx.fillRect(0, 0, W, H);
    if (dusk < 0.3) return;
    const glow = clamp((dusk - 0.3) / 0.3, 0, 1);
    ctx.globalCompositeOperation = "lighter";
    const lights = [...LAMPS.map(([x, y]) => [x, y - 39, 64]), [P.adoption.x + 28, P.adoption.y - 28, 40],
      [P.cache.x + 30, P.cache.y - 44, 34], [P.owl.x, P.owl.y - 50, 90]];
    for (const [x, y, radius] of lights) {
      const light = ctx.createRadialGradient(x, y, 2, x, y, radius);
      light.addColorStop(0, `rgba(255,214,120,${0.55 * glow})`);
      light.addColorStop(1, "rgba(255,214,120,0)");
      ctx.fillStyle = light;
      ctx.fillRect(x - radius, y - radius, radius * 2, radius * 2);
    }
    for (let i = 0; i < 16; i += 1) {
      const x = (i * 197) % W + Math.sin(time * 0.6 + i) * 30;
      const y = 140 + ((i * 131) % 520) + Math.cos(time * 0.5 + i * 2) * 20;
      const pulse = (Math.sin(time * 2 + i * 1.7) + 1) / 2;
      A.oval(ctx, x, y, 2.4, 2.4, `rgba(255,240,150,${glow * pulse})`);
    }
    ctx.globalCompositeOperation = "source-over";
  }

  /* Labels on top */

  drawSigns(ctx, time) {
    const game = this.game;
    for (const id of SYSTEM_IDS) {
      const sign = SIGNS[id];
      const system = SYSTEMS[id];
      const built = game.online(id);
      const width = A.measure(ctx, system.label, 13, 800) + 42;
      const shake = this.shakeSign[id] > time ? Math.sin(time * 50) * 3 : 0;
      const x = sign.x - width / 2 + shake;
      A.rrect(ctx, x, sign.y - 12, width, 24, 12, built ? "#ffffff" : "#efeaf4", built ? A.OUTLINE : "#9a8fa6", 2);
      A.oval(ctx, x + 13, sign.y, 12, 12, built ? system.color : "#b3abbd", built ? A.OUTLINE : "#9a8fa6", 2);
      A.text(ctx, id, x + 13, sign.y + 1, { size: 11, color: "#ffffff", weight: 800 });
      A.text(ctx, system.label, x + 29, sign.y + 1,
        { size: 13, color: built ? A.OUTLINE : "#8c8298", weight: 800, align: "left" });
      this.hits.unshift({ key: `sign:${id}`, x: sign.x - width / 2, y: sign.y - 14, w: width, h: 28,
        tip: `${id} ${system.label}: ${built ? system.with : system.without}`, action: null });
    }
  }

  drawWaits(ctx, time) {
    this.waits = this.waits.filter((wait) => time - wait.start < wait.seconds);
    for (const wait of this.waits) {
      const k = (time - wait.start) / wait.seconds;
      const y = wait.y + 26;
      A.oval(ctx, wait.x, y, 15, 15, "#ffffff", A.OUTLINE, 2.5);
      ctx.beginPath();
      ctx.moveTo(wait.x, y);
      ctx.arc(wait.x, y, 11, -Math.PI / 2, -Math.PI / 2 + k * Math.PI * 2);
      ctx.closePath();
      ctx.fillStyle = SYSTEMS["06"].color;
      ctx.fill();
    }
  }

  drawCallouts(ctx, time) {
    this.callouts = this.callouts.filter((callout) => time - callout.born < 3.8);
    for (const callout of this.callouts) {
      const age = time - callout.born;
      const system = SYSTEMS[callout.id];
      const tab = `${callout.id} ${system.label.toUpperCase()}`;
      const tabWidth = A.measure(ctx, tab, 12, 800) + 20;
      const width = tabWidth + A.measure(ctx, callout.text, 14, 700) + 44;
      const height = 30;
      const direction = callout.below ? 1 : -1;
      const x = clamp(callout.x, width / 2 + 8, W - width / 2 - 8);
      const y = Math.max(92, callout.y + direction * (callout.slot * 34 + height / 2 + Math.min(age, 1) * 5));
      const pop = age < 0.2 ? 0.5 + (age / 0.2) * 0.62 : age < 0.3 ? 1.12 - ((age - 0.2) / 0.1) * 0.12 : 1;

      ctx.save();
      ctx.globalAlpha = age > 3.4 ? (3.8 - age) / 0.4 : 1;
      ctx.translate(x, y);
      ctx.scale(pop, pop);
      A.rrect(ctx, -width / 2 + 2, -height / 2 + 4, width, height, 15, "rgba(40,30,60,0.25)");
      A.rrect(ctx, -width / 2, -height / 2, width, height, 15, callout.good ? "#ffffff" : "#fff1f1",
        callout.good ? A.OUTLINE : "#d13b40", 2.5);
      ctx.save();
      ctx.beginPath();
      ctx.roundRect(-width / 2 + 1.5, -height / 2 + 1.5, width - 3, height - 3, 13.5);
      ctx.clip();
      ctx.fillStyle = system.color;
      ctx.fillRect(-width / 2, -height / 2, tabWidth, height);
      ctx.restore();
      A.text(ctx, tab, -width / 2 + tabWidth / 2 + 1, 1, { size: 12, color: "#ffffff", weight: 800 });
      A.text(ctx, callout.text, -width / 2 + tabWidth + 9, 1,
        { size: 14, color: callout.good ? A.OUTLINE : "#b3262b", align: "left" });
      const ix = width / 2 - 16;
      A.oval(ctx, ix, 0, 9, 9, callout.good ? "#3fbf6f" : "#e5484d");
      if (callout.good) A.line(ctx, [ix - 4, 0, ix - 1, 3.5, ix + 4.5, -3.5], "#ffffff", 2.5);
      else {
        A.line(ctx, [ix - 3.5, -3.5, ix + 3.5, 3.5], "#ffffff", 2.5);
        A.line(ctx, [ix - 3.5, 3.5, ix + 3.5, -3.5], "#ffffff", 2.5);
      }
      ctx.restore();
    }
  }

  drawHover(ctx, time) {
    const hit = this.target(this.pointer);
    this.canvas.style.cursor = hit ? (hit.action ? "pointer" : "help") : "default";
    this.tip.hidden = !hit;
    if (!hit) return;
    if (hit.action) {
      ctx.save();
      ctx.setLineDash([8, 7]);
      ctx.lineDashOffset = -time * 24;
      A.rrect(ctx, hit.x - 3, hit.y - 3, hit.w + 6, hit.h + 6, 16, "rgba(255,255,255,0.12)", "#ffffff", 3);
      ctx.restore();
    }
    if (this.tip.textContent !== hit.tip) this.tip.textContent = hit.tip;
    const flipX = this.pointer.cssX > this.canvas.clientWidth - 280;
    this.tip.style.left = flipX ? "" : `${this.pointer.cssX + 16}px`;
    this.tip.style.right = flipX ? `${this.canvas.clientWidth - this.pointer.cssX + 12}px` : "";
    this.tip.style.top = `${this.pointer.cssY + 18}px`;
  }

  syncSpeech() {
    const speech = this.game.speech;
    this.speech.hidden = !speech.text;
    this.speech.dataset.state = speech.state;
    if (this.speech.textContent !== speech.text) this.speech.textContent = speech.text;
  }
}
