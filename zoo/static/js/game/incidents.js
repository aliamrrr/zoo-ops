/** The incidents of a shift (pigeons, storm, raccoon, bad release) and the pager. */
import { $ } from "../dom.js";
import { renderPins } from "./hud.js";
import { PAGER_LEAD, STORM_SECONDS } from "./rules.js";

export function tickIncidents(game) {
  for (const incident of game.incidents) {
    if (!incident.paged && game.online("05") && game.t >= incident.at - PAGER_LEAD) {
      incident.paged = true;
      page(game, incident.soon);
    }
    if (!incident.done && game.t >= incident.at) {
      incident.done = true;
      if (!game.online("05")) game.emit("05", false, "No alert: you did not see it coming");
      game[incident.kind]();
      renderPins(game);
    }
  }
  if (game.pagerUntil && game.t >= game.pagerUntil) {
    game.pagerUntil = 0;
    $("#pager").hidden = true;
  }
  if (game.stormUntil && game.t >= game.stormUntil) {
    game.stormUntil = 0;
    game.log("The storm is over. The bridge to the Owl is open again.");
  }
}

export function page(game, text) {
  const pager = $("#pager");
  pager.textContent = `Mika's pager: ${text}`;
  pager.hidden = false;
  game.pagerUntil = game.t + PAGER_LEAD + 2;
  game.sfx("chirp");
  game.emit("05", true, `Pager: ${text}`);
}

export function pigeons(game) {
  const blocked = game.online("02");
  game.pigeonsEvent = { at: game.t, blocked, left: 10 };
  if (blocked) {
    const admitted = game.systems["02"]?.metrics?.["pigeons admitted"] ?? "a few";
    game.earn(-1, "kiosk");
    game.sfx("honk");
    game.say("goose", "HONK! One at a time!", 3);
    game.emit("02", true, `Rate limit: ${admitted} of 500 requests pass`);
    game.log(`A pigeon swarm hits the gate. Gus throttles it: ${admitted} requests out of ` +
      "500 reach the Owl, visitors keep flowing.", "good", "02");
  } else {
    game.jammedUntil = game.t + 12;
    game.earn(-10, "kiosk");
    game.hurt("02", 4);
    game.sfx("bad");
    game.emit("02", false, "No rate limit: 500 requests jam the kiosk");
    game.log("A pigeon swarm floods the Owl with 500 requests. The kiosk is jammed and the " +
      "bill goes up by 10 coins.", "bad", "02");
  }
}

export function storm(game) {
  game.stormUntil = game.t + STORM_SECONDS;
  game.sfx("thunder");
  game.fx("shake", { amount: 10 });
  game.log("A storm floods the bridge to the Owl. Questions need another way through.", "warn");
}

export function raccoon(game) {
  const blocked = game.online("09");
  game.raccoonEvent = { at: game.t, blocked, scares: 0, fledAt: null };
  if (blocked) {
    game.after(2.2, () => {
      game.earn(5, "chest");
      game.sfx("bark");
      game.say("dog", "WOOF! Wrong shelter!", 3);
      game.emit("09", true, "Badge refused: wrong tenant, access denied");
    });
    game.log("A raccoon from another shelter shows a forged badge. Rex refuses it. " +
      "Security bonus: 5 coins.", "good", "09");
  } else {
    const stolen = Math.max(0, Math.floor(game.coins * 0.3));
    game.emit("09", false, "No auth check: a raccoon got in. Click it!");
    game.after(4.2, () => {
      if (game.raccoonEvent.fledAt !== null) return;
      game.earn(-stolen, "chest");
      game.hurt("09", 5);
      game.sfx("bad");
      game.log(`A raccoon walked in with a forged badge and stole ${stolen} coins.`, "bad", "09");
    });
  }
}

export function release(game) {
  const caught = game.online("10");
  game.releaseEvent = { at: game.t, caught };
  if (caught) {
    game.rep -= 1;
    game.sfx("chirp");
    game.say("canary", "v2 sounds wrong. Rollback!", 3.5);
    game.emit("10", true, "Canary release: v2 fails on 10%, rolled back");
    game.log("Kiosk v2 went to the canary first. Pip heard the errors and rolled it back.",
      "good", "10");
  } else {
    game.brokenReleaseUntil = game.t + 15;
    game.hurt("10", 3);
    game.sfx("bad");
    game.fx("shake", { amount: 6 });
    game.emit("10", false, "No canary: v2 ships to everyone and breaks");
    game.log("Kiosk v2 shipped to everyone at once. It is broken for the next 15 seconds.",
      "bad", "10");
  }
}

export function closing(game) {
  const waiting = game.visitors.filter((visitor) => visitor.state === "waiting");
  if (!waiting.length) return;
  if (game.online("10")) {
    game.earn(3 * waiting.length, "kiosk");
    game.served += waiting.length;
    game.emit("10", true, "Graceful shutdown: the line is drained");
    game.log(`Closing time: the kiosk drains gracefully, ${waiting.length} visitors served.`,
      "good", "10");
  } else {
    game.lost += waiting.length;
    game.hurt("10", 3 * waiting.length);
    game.emit("10", false, "Hard stop: the line is dropped");
    game.log(`Closing time: the kiosk stopped dead, ${waiting.length} visitors dropped.`,
      "bad", "10");
  }
}
