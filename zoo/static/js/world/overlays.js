/** Labels on top of the zoo: signs, wait bars, callouts, hover tips and speech bubbles. */
import * as A from "../art.js";
import { SIGNS, W } from "../scenery.js";
import { SYSTEM_IDS, SYSTEMS } from "../systems.js";
import { clamp } from "./motion.js";

export function drawSigns(world, ctx, time) {
  const game = world.game;
  for (const id of SYSTEM_IDS) {
    const sign = SIGNS[id];
    const system = SYSTEMS[id];
    const built = game.online(id);
    const width = A.measure(ctx, system.label, 13, 800) + 42;
    const shake = world.shakeSign[id] > time ? Math.sin(time * 50) * 3 : 0;
    const x = sign.x - width / 2 + shake;
    A.rrect(ctx, x, sign.y - 12, width, 24, 12, built ? "#ffffff" : "#efeaf4", built ? A.OUTLINE : "#9a8fa6", 2);
    A.oval(ctx, x + 13, sign.y, 12, 12, built ? system.color : "#b3abbd", built ? A.OUTLINE : "#9a8fa6", 2);
    A.text(ctx, id, x + 13, sign.y + 1, { size: 11, color: "#ffffff", weight: 800 });
    A.text(ctx, system.label, x + 29, sign.y + 1,
      { size: 13, color: built ? A.OUTLINE : "#8c8298", weight: 800, align: "left" });
    world.hits.unshift({ key: `sign:${id}`, x: sign.x - width / 2, y: sign.y - 14, w: width, h: 28,
      tip: `${id} ${system.label}: ${built ? system.with : system.without}`, action: null });
  }
}

export function drawWaits(world, ctx, time) {
  world.waits = world.waits.filter((wait) => time - wait.start < wait.seconds);
  for (const wait of world.waits) {
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

export function drawCallouts(world, ctx, time) {
  world.callouts = world.callouts.filter((callout) => time - callout.born < 3.8);
  for (const callout of world.callouts) {
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

export function drawHover(world, ctx, time) {
  const hit = world.target(world.pointer);
  world.canvas.style.cursor = hit ? (hit.action ? "pointer" : "help") : "default";
  world.tip.hidden = !hit;
  if (!hit) return;
  if (hit.action) {
    ctx.save();
    ctx.setLineDash([8, 7]);
    ctx.lineDashOffset = -time * 24;
    A.rrect(ctx, hit.x - 3, hit.y - 3, hit.w + 6, hit.h + 6, 16, "rgba(255,255,255,0.12)", "#ffffff", 3);
    ctx.restore();
  }
  if (world.tip.textContent !== hit.tip) world.tip.textContent = hit.tip;
  const flipX = world.pointer.cssX > world.canvas.clientWidth - 280;
  world.tip.style.left = flipX ? "" : `${world.pointer.cssX + 16}px`;
  world.tip.style.right = flipX ? `${world.canvas.clientWidth - world.pointer.cssX + 12}px` : "";
  world.tip.style.top = `${world.pointer.cssY + 18}px`;
}

export function syncSpeech(world) {
  const speech = world.game.speech;
  world.speech.hidden = !speech.text;
  world.speech.dataset.state = speech.state;
  if (world.speech.textContent !== speech.text) world.speech.textContent = speech.text;
}
