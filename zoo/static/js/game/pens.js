/** The pens: hunger, dirt, sickness, and the adoption window at the pink cottage. */
import { pick, random } from "./helpers.js";
import { ADOPTION_WINDOW, DIRT_EVERY, HUNGER_DECAY, HUNGRY_AT } from "./rules.js";

export function tickPens(game, dt) {
  if (game.t >= game.nextDirt) {
    const clean = game.pens.filter((pen) => !pen.dirty);
    if (clean.length) {
      const pen = pick(clean);
      pen.dirty = true;
      pen.dirtSpot = { x: random(0.25, 0.75), y: random(0.5, 0.8) };
      if (game.online("08")) {
        pen.cleanAt = game.t + 4.5;
        pen.antsSince = game.t;
        game.emit("08", true, `Background job: the ants clean ${pen.name}'s pen`);
      } else {
        game.emit("08", false, "No workers: clean it by hand", `pen:${pen.id}`);
        game.log(`${pen.name}'s pen is dirty. Click the dirt to clean it by hand.`, "warn", "08");
      }
    }
    game.nextDirt = game.t + DIRT_EVERY;
  }
  for (const pen of game.pens) {
    if (pen.sick > 0) {
      pen.sick -= dt;
      if (pen.sick <= 0) game.log(`${pen.name} feels better.`);
    }
    pen.hunger = Math.max(0, pen.hunger - HUNGER_DECAY * dt);
    if (pen.hunger < HUNGRY_AT) game.rep -= 0.25 * dt;
    if (pen.dirty) game.hurt(game.online("08") ? null : "08", 0.12 * dt);
    if (pen.dirty && pen.cleanAt !== null && game.t >= pen.cleanAt) {
      pen.dirty = false;
      pen.cleanAt = null;
      pen.antsSince = null;
      game.fx("clean", { pen: pen.id });
    }
  }
}

export function tag(game, pen, text, seconds = 2.5) {
  pen.tag = text;
  pen.tagUntil = game.t + seconds;
}

export function tickAdoption(game) {
  if (game.adoptions.length && game.t >= game.adoptions[0]) {
    game.adoptions.shift();
    game.adoption = { deadline: game.t + ADOPTION_WINDOW, since: game.t, pending: false };
    game.sfx("pop");
    game.log("Two families want to adopt Pixel the kitten. Click the pink cottage.", "warn");
  }
  if (game.adoption && !game.adoption.pending && game.t >= game.adoption.deadline) {
    game.adoption = null;
    game.hurt(null, 4);
    game.log("The families gave up waiting at the adoption office.", "bad");
  }
}
