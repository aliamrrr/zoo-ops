/** The title, pause and result screens of a shift, and the mode picker. */
import { critterCanvas } from "../art.js";
import { $, el, patternChip } from "../dom.js";
import { CLASSIC } from "../mode.js";
import { SYSTEM_IDS, SYSTEMS } from "../systems.js";
import { readNumber, writeNumber } from "./helpers.js";
import { pigeons, raccoon } from "./incidents.js";
import { STAR_SCORES } from "./rules.js";

export function finish(game, reason, won) {
  clearInterval(game.timer);
  game.state = "over";
  const score = Math.max(0, Math.round(game.coins)) + Math.round(game.rep) * 3 + game.served * 2;
  const stars = STAR_SCORES.filter((needed) => score >= needed).length;
  const best = readNumber(game.bestKey, 0);
  if (score > best) writeNumber(game.bestKey, score);
  if (won) writeNumber(game.dayKey, game.day + 1);
  game.sfx(won ? "win" : "lose");
  if (won) game.fx("confetti");

  const worst = Object.entries(game.blame).sort((a, b) => b[1] - a[1]).slice(0, 3);
  const lessons = worst.length
    ? el("ul", { class: "lessons" }, worst.map(([id, cost]) => {
      const chip = patternChip(id, "button");
      chip.addEventListener("click", () => game.onOpenStation(id));
      return el("li", {}, [chip, el("span", { text: `cost you ${Math.round(cost)} points` })]);
    }))
    : el("p", { class: "muted", text: "No system let you down. Flawless backend." });
  overlay(game, [
    el("p", { class: "eyebrow", text: won ? `Day ${game.day} complete` : reason }),
    el("div", { class: "stars", "aria-label": `${stars} of 3 stars` }, [0, 1, 2].map((i) =>
      el("span", { class: "star", "data-on": String(i < stars) }))),
    el("div", { class: "score", text: String(score) }),
    el("p", { class: "muted", text: score > best ? "New best score!" : `Best so far: ${best}` }),
    el("dl", { class: "stats" }, [
      stat(game, "Coins", Math.round(game.coins)),
      stat(game, "Reputation", Math.round(game.rep)),
      stat(game, "Visitors served", `${game.served} / ${game.served + game.lost}`),
    ]),
    el("h2", { class: "overlay-title", text: "What cost you the most" }),
    lessons,
  ], [[won ? `Start day ${game.day + 1}` : "Try game day again", () => game.start(),
    "button-primary"]]);
}

export function readDay(game) {
  return Math.max(1, readNumber(game.dayKey, 1));
}

export function stat(game, label, value) {
  return el("div", {}, [el("dt", { text: label }), el("dd", { text: String(value) })]);
}

export function modePicker(game) {
  return el("div", { class: "modes", role: "radiogroup", "aria-label": "Difficulty" },
    game.modes.map((mode) => {
      const active = mode.key === game.mode.key;
      const card = el("button", {
        class: "mode-card", type: "button", role: "radio", "data-mode": mode.key,
        "aria-checked": String(active),
      }, [
        el("span", { class: "mode-title", text: mode.title }),
        el("span", { class: "mode-tagline", text: mode.tagline }),
      ]);
      if (!active) card.addEventListener("click", () => game.onSwitchMode(mode.key));
      return card;
    }));
}

export function systemsLine(game, known) {
  if (!known) return "Running the morning backend check...";
  const checking = SYSTEM_IDS.filter((id) => game.systems[id]?.status === "checking").length;
  if (checking) return "Running the acceptance tests of every ticket...";
  const built = `${game.onlineCount()} of 10 backend patterns`;
  return game.mode.key === CLASSIC
    ? `${built} built. Each one you code wakes up a keeper.`
    : `${built} in production. A ticket ships when its tests pass and its block is on the Blueprint.`;
}

export function showIntro(game) {
  const known = Object.keys(game.systems).length > 0;
  const cast = el("div", { class: "cast" }, ["rabbit", "owl", "panda", "fox", "penguin"].map(
    (kind, i) => critterCanvas(kind, i === 2 ? 96 : 68)));
  const dots = el("div", { class: "system-dots" }, SYSTEM_IDS.map((id) =>
    el("i", { "data-on": String(game.online(id)), style: `--chip:${SYSTEMS[id].color}`,
      title: `${id} ${SYSTEMS[id].label}` })));
  overlay(game, [
    cast,
    el("h1", { class: "logo", text: game.mode.title }),
    el("p", { class: "tagline", text: `Day ${readDay(game)}. You are Bao, the panda keeper.` }),
    el("ul", { class: "howto" }, [
      el("li", { text: "Click a visitor, an animal, dirt or the pink cottage: Bao walks there and does the job. Plan his route!" }),
      el("li", { text: "Serve visitors in a row to build a combo. Golden VIPs pay triple but hate waiting." }),
      el("li", { text: "A keeper is asleep? Do its job by hand: click pigeons to shoo them, click the raccoon to scare it." }),
    ]),
    el("div", { class: "systems-line" }, [
      dots,
      el("span", { text: systemsLine(game, known) }),
    ]),
    modePicker(game),
  ], [["Open the gates", () => game.start(), "button-primary button-big"]], !known);
}

export function overlay(game, children, actions, disabled = false) {
  const buttons = actions.map(([label, action, style]) => {
    const button = el("button", { class: `button ${style}`, type: "button", text: label });
    button.disabled = disabled;
    button.addEventListener("click", action);
    return button;
  });
  $("#overlay-card").replaceChildren(...children, el("div", { class: "overlay-actions" }, buttons));
  $("#overlay").hidden = false;
  buttons[0]?.focus();
}
