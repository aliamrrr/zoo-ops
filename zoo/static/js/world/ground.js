/** Ground level: the pond and what lies on the paths. */
import * as A from "../art.js";
import { P, paintAcorns, paintConstruction, PENS } from "../scenery.js";
import { SYSTEM_IDS } from "../systems.js";
import { penDoor } from "./actors.js";
import { between, clamp, TAPES } from "./motion.js";

export function drawWater(world, ctx, time) {
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
  if (world.game.t < world.game.stormUntil) {
    const swell = Math.sin(time * 3) * 3;
    A.rrect(ctx, 606, 318 + swell, 68, 78, 14, "rgba(70,150,220,0.72)");
    for (let i = 0; i < 3; i += 1) {
      A.line(ctx, [614, 334 + i * 22 + swell, 628, 330 + i * 22 + swell, 642, 334 + i * 22 + swell,
        656, 330 + i * 22 + swell, 668, 334 + i * 22 + swell], "rgba(255,255,255,0.8)", 2.5);
    }
  }
}

export function drawGroundThings(world, ctx, time) {
  const game = world.game;
  if (game.online("01")) paintAcorns(ctx, game.askedTopics.size);
  for (const id of SYSTEM_IDS) {
    if (game.online(id) || !Object.keys(game.systems).length) continue;
    const [x, y, width] = TAPES[id];
    paintConstruction(ctx, x, y, width);
    A.cone(ctx, x + width / 2 + 14, y + 12, 13);
  }

  if (game.t < game.brokenReleaseUntil) {
    world.hit("rollback", P.owl.x - 110, P.owl.y - 110, 220, 150, "Roll the kiosk back to v1",
      () => game.enqueue("rollback", () => P.bridgeFoot, () => game.rollback(),
        { valid: () => game.t < game.brokenReleaseUntil }));
    A.bubble(ctx, "click to roll back!", P.owl.x + 96, P.owl.y - 8 + Math.sin(time * 6) * 2, { size: 13 });
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
      ant(world, ctx, P.anthill.x + Math.cos(angle) * 52, P.anthill.y + 4 + Math.sin(angle) * 9, 1);
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
        ant(world, ctx, point.x, point.y + Math.sin(k * 40) * 2, 1);
      }
    } else {
      world.hit(`dirt:${pen.id}`, x - 20, y - 26, 40, 40, `Clean ${pen.name}'s pen`,
        () => game.enqueue(`dirt:${pen.id}`, () => penDoor(world, pen.id), () => game.clean(pen),
          { valid: () => pen.dirty && pen.cleanAt === null }));
    }
  }
}

export function ant(world, ctx, x, y, s) {
  A.oval(ctx, x - 3 * s, y, 2.2 * s, 1.8 * s, "#6e2f2b");
  A.oval(ctx, x, y, 1.8 * s, 1.5 * s, "#6e2f2b");
  A.oval(ctx, x + 3 * s, y, 2 * s, 1.7 * s, "#6e2f2b");
}
