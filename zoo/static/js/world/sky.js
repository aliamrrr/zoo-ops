/** Above the zoo: things in flight, the weather and the light. */
import * as A from "../art.js";
import { SHIFT_SECONDS } from "../game/rules.js";
import { H, LAMPS, P, W } from "../scenery.js";
import { along, between, clamp, lerp } from "./motion.js";

export function canaryFlying(world) {
  const event = world.game.releaseEvent;
  return event && event.caught && world.game.t - event.at < 4.8;
}

export function drawFlyers(world, ctx, time) {
  const game = world.game;
  const flap = (seed) => (Math.sin(time * 20 + seed) + 1) / 2;

  const pigeons = game.pigeonsEvent;
  if (pigeons) {
    const age = game.t - pigeons.at;
    const limit = pigeons.blocked ? 4.6 : 15;
    const flock = pigeons.blocked ? 10 : pigeons.left;
    for (let i = 0; i < flock && age < limit; i += 1) {
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
      const px = point.x + wobble.x;
      const py = point.y + wobble.y;
      A.drawCritter(ctx, "pigeon", px, py, 34,
        { time, shadow: false, flap: flap(i), flip: i % 2 === 0, eyes: pigeons.blocked && age > 1.3 ? "sad" : "open" });
      if (!pigeons.blocked && age < 12) {
        world.hit(`pigeon:${i}`, px - 24, py - 44, 48, 52, "Shoo!", () => {
          world.fx.burst("puff", px, py - 18, 6);
          game.shooPigeon();
        });
      }
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

  world.flights = world.flights.filter((flight) => {
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

export function drawWeather(world, ctx, time) {
  const game = world.game;
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

export function drawLight(world, ctx, time) {
  const day = clamp(world.game.t / SHIFT_SECONDS, 0, 1);
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
