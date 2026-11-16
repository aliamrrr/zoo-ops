/** Turns the game's events into animations: callouts, coins, flights and sounds. */
import { P, PENS, SIGNS } from "../scenery.js";
import { SYSTEMS } from "../systems.js";

export function anchor(world, anchor, id) {
  if (anchor && typeof anchor === "object") {
    const position = world.positions.get(anchor.visitor) || P.serve;
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

export function handle(world, event, time) {
  switch (event.type) {
    case "moment": {
      const point = anchor(world, event.anchor, event.id);
      for (const other of world.callouts) {
        if (Math.abs(other.x - point.x) < 200 && Math.abs(other.y - point.y) < 40) other.slot += 1;
      }
      world.callouts.push({ ...event, ...point, slot: 0, born: time });
      if (event.good) {
        world.cheer[event.id] = time + 1.4;
        world.fx.burst("spark", point.x, point.y - 8, 7, SYSTEMS[event.id].color);
        world.sfx.play("good");
      } else {
        world.shakeSign[event.id] = time + 0.7;
        world.fx.burst("puff", point.x, point.y - 4, 5, "rgba(229,72,77,0.5)");
        world.sfx.play("bad");
      }
      break;
    }
    case "coins": {
      const point = anchor(world, event.anchor, "01");
      const gain = event.amount > 0;
      world.fx.pop(`${gain ? "+" : ""}${event.amount}`, point.x, point.y + 10,
        gain ? "#ffd23f" : "#ff8a8a", gain ? 24 : 20);
      if (gain) world.fx.burst("coin", point.x, point.y + 20, Math.min(8, event.amount));
      break;
    }
    case "happy": {
      const position = world.positions.get(event.visitor);
      if (position) world.fx.burst("heart", position.x, position.y - 50, 6);
      break;
    }
    case "toss": {
      const to = world.positions.get(event.visitor) || P.serve;
      world.flights.push({ icon: "acorn", from: { x: P.cache.x, y: P.cache.y - 60 },
        to: { x: to.x, y: to.y - 40 }, start: time, duration: 0.5, arc: 70,
        land: () => world.fx.burst("spark", to.x, to.y - 44, 8, "#ffd23f") });
      break;
    }
    case "deliver":
      deliver(world, event, time);
      break;
    case "clean": {
      const pen = PENS[event.pen];
      world.fx.burst("spark", pen.x + pen.w / 2, pen.y + pen.h / 2 + 20, 12, "#ffffff");
      world.sfx.play("good");
      break;
    }
    case "wait":
      world.waits.push({ ...anchor(world, event.anchor, "06"), start: time, seconds: event.seconds });
      break;
    case "combo":
      world.fx.pop(`Combo x${event.level}!`, world.keeper.x, world.keeper.y - 84, "#ffd23f", 26);
      world.fx.burst("spark", world.keeper.x, world.keeper.y - 60, 10, "#ffd23f");
      world.sfx.play("good");
      break;
    case "shake":
      world.fx.shake = event.amount;
      break;
    case "confetti":
      for (const x of [240, 520, 760, 1040]) world.fx.burst("confetti", x, 420, 26);
      break;
    case "sfx":
      world.sfx.play(event.name);
      break;
    default:
  }
}

/** One order: tickets fly to the kitchen (one per network try), bowls fly back. */
export function deliver(world, event, time) {
  const animal = world.animals[event.pen];
  const kitchen = { x: P.kitchen.x, y: P.kitchen.y - 56 };
  const mouth = { x: animal.x, y: animal.y - 40 };
  for (let i = 0; i < event.attempts; i += 1) {
    world.flights.push({ icon: "ticket", from: mouth, to: kitchen, start: time + i * 0.2,
      duration: 0.4, arc: 40 });
  }
  const cooked = time + event.attempts * 0.2 + 0.35;
  for (let i = 0; i < event.meals; i += 1) {
    world.flights.push({ icon: "bowl", from: kitchen, to: mouth, start: cooked + i * 0.28,
      duration: 0.5, arc: 60, land: () => {
        world.fx.burst("crumb", mouth.x, mouth.y + 14, 6, "#c98e52");
        world.fx.burst("heart", mouth.x, mouth.y - 20, i === 0 ? 3 : 0);
        world.sfx.play("munch");
        if (i > 0) world.fx.pop(`x${i + 1}!`, mouth.x + 26, mouth.y - 34, "#ff8a8a", 22);
      } });
  }
  if (event.meals === 1 && event.attempts > 1) {
    world.flights.push({ icon: "none", from: kitchen, to: kitchen, start: cooked, duration: 0.1,
      arc: 0, land: () => world.fx.pop(`${event.attempts - 1} retry ignored`, kitchen.x,
        kitchen.y - 40, "#9be28a", 16) });
  }
}
