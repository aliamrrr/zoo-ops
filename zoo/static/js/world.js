/**
 * The living zoo: draws the game state every frame on top of the painted scenery and turns
 * clicks into game actions. Game rules live in game.js; this file only shows them.
 */
import { Fx } from "./fx.js";
import { H, P, paintGateFront, paintScenery, PENS, W } from "./scenery.js";
import { addAdoption, addKeeper, addKeepers, addOwl, addPens, addRaccoon, addVisitors } from "./world/actors.js";
import { handle } from "./world/events.js";
import { drawGroundThings, drawWater } from "./world/ground.js";
import { drawCallouts, drawHover, drawSigns, drawWaits, syncSpeech } from "./world/overlays.js";
import { drawFlyers, drawLight, drawWeather } from "./world/sky.js";

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
    this.keeper = { x: 600, y: 540, flip: false, waiting: 0 };
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

    for (const event of game.events.splice(0)) handle(this, event, time);
    this.fx.update(dt);
    const [shakeX, shakeY] = this.fx.offset();

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.drawImage(this.background, 0, 0);
    ctx.setTransform(this.scale, 0, 0, this.scale, shakeX * this.scale, shakeY * this.scale);
    ctx.lineJoin = "round";
    this.hits = [];

    drawWater(this, ctx, time);
    drawGroundThings(this, ctx, time);
    const actors = [];
    addKeepers(this, actors, ctx, time, move);
    addOwl(this, actors, ctx, time);
    addPens(this, actors, ctx, time, move);
    addVisitors(this, actors, ctx, time, move);
    addAdoption(this, actors, ctx, time);
    addRaccoon(this, actors, ctx, time);
    addKeeper(this, actors, ctx, time, move);
    actors.sort((a, b) => a.y - b.y);
    for (const actor of actors) actor.draw();
    const small = (hit) => (hit.key.startsWith("dirt") ? 1 : 0);
    this.hits.sort((a, b) => small(a) - small(b));

    paintGateFront(ctx, time);
    drawFlyers(this, ctx, time);
    this.fx.draw(ctx);
    drawWeather(this, ctx, time);
    drawLight(this, ctx, time);
    drawSigns(this, ctx, time);
    drawWaits(this, ctx, time);
    drawCallouts(this, ctx, time);
    if (game.state !== "running") this.hits = [];
    drawHover(this, ctx, time);
    syncSpeech(this);
  }

}
