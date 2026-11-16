/** Everything that moves on the ground, drawn back to front: keepers, Owl, animals, visitors, Bao. */
import * as A from "../art.js";
import { HUNGRY_AT } from "../game/rules.js";
import { P, PENS } from "../scenery.js";
import { along, between, blinking, clamp, hop, KEEPERS, moveToward } from "./motion.js";
import { canaryFlying } from "./sky.js";

export function addKeepers(world, actors, ctx, time, move) {
  const game = world.game;
  const known = Object.keys(game.systems).length > 0;
  KEEPERS.forEach((keeper, index) => {
    const built = game.online(keeper.id);
    const said = game.bubbles[keeper.who];
    const talking = said && said.until > game.t;
    const cheering = world.cheer[keeper.id] > time;
    let { x, y } = keeper.spot;
    const options = { time, shadow: !keeper.perched };

    if (keeper.who === "fox") {
      stepFox(world, move);
      ({ x, y } = world.fox);
      options.flip = world.fox.flip;
      if (world.fox.moving) options.lift = hop(time);
      if (world.fox.carrying) {
        options.carry = (c, u) => A.envelope(c, 0.27 * u, -0.3 * u, 0.13 * u);
      }
    }
    if (keeper.who === "canary" && canaryFlying(world)) return;
    if (keeper.who === "mole" && game.t < game.diggingUntil) {
      options.squash = Math.sin(time * 26) * 0.06;
      if (Math.random() < 0.3) world.fx.burst("dirt", x + (Math.random() - 0.5) * 50, y - 6, 1);
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

export function stepFox(world, move) {
  const game = world.game;
  const trip = game.trip;
  let target = P.fox;
  world.fox.carrying = false;
  if (game.online("03") && trip && trip.provider !== "cache" && game.t - trip.since > 0.12) {
    world.fox.carrying = true;
    const storm = game.t < game.stormUntil;
    if (trip.provider === "parrot") target = P.perchFoot;
    else if (storm) target = game.t - trip.since < 1.3 ? P.bridgeFoot : P.perchFoot;
    else target = P.bridgeTop;
  }
  world.fox.moving = moveToward(world.fox, target, 300, move);
  if (!world.fox.moving && target === P.fox) world.fox.flip = true;
}

export function addOwl(world, actors, ctx, time) {
  const game = world.game;
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
      world.fx.burst("spark", P.owl.x + (Math.random() - 0.5) * 70, P.owl.y - 60, 1, "#ff8a8a");
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
        world.fx.burst("splash", 640, 356, 12);
        world.sfx.play("splash");
      }
    } else if (age < 0.9) {
      const point = along(route, age / 0.9);
      actors.push({ y: 720, draw: () => A.envelope(ctx, point.x, point.y - 8 - Math.sin(age * 12) * 3, 10) });
    }
  }
}

export function addPens(world, actors, ctx, time, move) {
  const game = world.game;
  const blind = !game.online("05");
  game.pens.forEach((pen, index) => {
    const box = PENS[pen.id];
    const animal = world.animals[pen.id];
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
    world.hit(`pen:${pen.id}`, box.x, box.y, box.w, box.h, tip,
      () => game.enqueue(`pen:${pen.id}`, () => penDoor(world, pen.id), () => game.feed(pen)));
  });
}

export function addVisitors(world, actors, ctx, time, move) {
  const game = world.game;
  const blind = !game.online("05");
  const waiting = game.visitors.filter((visitor) => visitor.state === "waiting");
  const seen = new Set();

  for (const visitor of game.visitors) {
    seen.add(visitor.id);
    if (!world.positions.has(visitor.id)) world.positions.set(visitor.id, { ...P.spawn, flip: false });
    const position = world.positions.get(visitor.id);
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
        const k = clamp(visitor.patience / visitor.maxPatience, 0, 1);
        A.rrect(ctx, position.x - 19, top, 38, 9, 4.5, "rgba(75,55,87,0.85)");
        if (k > 0.05) {
          A.rrect(ctx, position.x - 17, top + 2, 34 * k, 5, 2.5,
            k < 0.3 ? "#ff6b6b" : k < 0.6 ? "#ffb347" : "#7fe07a");
        }
      }
      if (upset) A.anger(ctx, position.x + 17, top - 6, 5);
      if (visitor.vip) {
        A.star(ctx, position.x, top - 12 + Math.sin(time * 5) * 2, 9, "#ffc93c");
        A.text(ctx, "VIP", position.x, top - 26, { size: 11, color: "#ffd23f", stroke: A.OUTLINE, weight: 800 });
      }
      if (front && !walking && !game.kioskBusy && game.t < 30) {
        const bounce = Math.sin(time * 6) * 4;
        A.poly(ctx, [position.x - 9, top - 26 + bounce, position.x + 9, top - 26 + bounce,
          position.x, top - 12 + bounce], "#ffd23f", A.OUTLINE, 2.5);
        A.text(ctx, "click me!", position.x, top - 38 + bounce,
          { size: 14, color: "#ffffff", stroke: A.OUTLINE, weight: 800 });
      }
    } });
    if (visitor.state === "waiting") {
      world.hit(`visitor:${visitor.id}`, position.x - 22, position.y - 60, 44, 64,
        `"${visitor.question}" Click to ask the Owl.`,
        () => game.enqueue(`visitor:${visitor.id}`, () => ({ x: position.x + 34, y: position.y + 8 }),
          () => game.serve(visitor),
          { valid: () => visitor.state === "waiting" && !visitor.gone, ready: () => !game.kioskBusy }));
    }
  }

  for (const departure of game.departures) {
    seen.add(departure.id);
    const position = world.positions.get(departure.id) || { ...P.serve, flip: false };
    world.positions.set(departure.id, position);
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
  for (const id of world.positions.keys()) if (!seen.has(id)) world.positions.delete(id);
}

export function addAdoption(world, actors, ctx, time) {
  const game = world.game;
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
    world.hit("adoption", cottage.x - 100, cottage.y - 110, 170, 150, "Approve the adoption",
      () => game.enqueue("adoption", () => ({ x: cottage.x + 8, y: cottage.y + 26 }),
        () => game.approveAdoption(), { valid: () => Boolean(game.adoption) }));
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

export function addRaccoon(world, actors, ctx, time) {
  const event = world.game.raccoonEvent;
  if (!event) return;
  const age = world.game.t - event.at;
  const lurk = { x: 836, y: 700 };
  const chest = { x: P.chest.x + 40, y: P.chest.y + 12 };
  let point;
  let options = { time, flip: true, lift: hop(time * 0.8) * 0.6 };
  let loot = false;
  if (event.fledAt !== null) {
    const fled = world.game.t - event.fledAt;
    if (fled > 1.3) return;
    const from = along([P.staffDoor, lurk, chest], (event.fledAt - event.at) / 4.2);
    point = between(from, { x: 960, y: 800 }, fled / 1.3);
    options = { time, flip: false, lift: hop(time * 1.6), eyes: "sad" };
  } else if (event.blocked) {
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
    if (!event.blocked && event.fledAt === null && age < 4.2) {
      A.bubble(ctx, `click! ${3 - event.scares}`, point.x, point.y - 62 + Math.sin(time * 8) * 2, { size: 13 });
    }
  } });
  if (!event.blocked && event.fledAt === null && age < 4.2) {
    world.hit("raccoon", point.x - 34, point.y - 64, 68, 74, "Scare the raccoon away!", () => {
      world.fx.burst("puff", point.x, point.y - 30, 5);
      world.game.scareRaccoon();
    });
  }
}

export function penDoor(world, id) {
  const box = PENS[id];
  return { x: box.x + box.w / 2, y: box.y < 300 ? box.y + box.h + 18 : box.y - 30 };
}

/** Bao, the player's keeper: walks to the first job in his list, does it, takes the next. */
export function addKeeper(world, actors, ctx, time, move) {
  const game = world.game;
  const keeper = world.keeper;
  while (game.tasks.length && !game.tasks[0].valid()) game.tasks.shift();
  const task = game.tasks[0];
  let walking = false;
  if (task) {
    walking = moveToward(keeper, task.point(), 290, move);
    if (!walking && move) {
      keeper.waiting += move;
      if (task.ready() || keeper.waiting > 5) {
        game.tasks.shift();
        keeper.waiting = 0;
        if (task.ready()) {
          task.run();
          world.fx.burst("puff", keeper.x, keeper.y - 6, 4);
        }
      }
    } else {
      keeper.waiting = 0;
    }
  }
  const points = game.tasks.map((item) => item.point());
  const said = game.bubbles.keeper;
  actors.push({ y: keeper.y, draw: () => {
    A.drawCritter(ctx, "panda", keeper.x, keeper.y, 60, { time, flip: keeper.flip,
      lift: walking ? hop(time * 1.2) : 0, eyes: blinking(time, 7) ? "blink" : "open",
      squash: walking ? 0 : Math.sin(time * 2.6) * 0.02 });
    if (said && said.until > game.t) A.bubble(ctx, said.text, keeper.x, keeper.y - 66, { size: 13 });
  } });
  if (points.length) {
    ctx.save();
    ctx.setLineDash([3, 9]);
    ctx.lineDashOffset = -time * 30;
    A.line(ctx, [keeper.x, keeper.y - 4, ...points.flatMap((point) => [point.x, point.y - 4])],
      "rgba(255,255,255,0.9)", 3.5);
    ctx.restore();
    points.forEach((point, index) => {
      A.oval(ctx, point.x, point.y - 4, 10, 10, "#58c96c", A.OUTLINE, 2.5);
      A.text(ctx, String(index + 1), point.x, point.y - 3, { size: 12, color: "#ffffff", weight: 800 });
    });
  }
}
