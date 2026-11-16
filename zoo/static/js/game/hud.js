/** The HUD over the zoo: coins, reputation, clock, forecast pins. */
import { $, el } from "../dom.js";
import { nearestRank } from "./helpers.js";
import { SHIFT_SECONDS } from "./rules.js";

export function renderPins(game) {
  const blind = !game.online("05");
  const pins = (game.incidents || []).map((incident) => el("i", {
    class: "pin",
    "data-done": String(incident.done),
    "data-blind": String(blind && !incident.done),
    style: `left:${(incident.at / SHIFT_SECONDS) * 100}%`,
    title: blind && !incident.done ? "Unknown. Build level 05 to see the forecast."
      : incident.label,
  }, [el("span", { text: blind && !incident.done ? "?" : incident.label })]));
  $("#day-pins").replaceChildren(...pins);
}

export function renderHud(game) {
  const blind = !game.online("05");
  const coins = $("#hud-coins");
  const value = String(Math.round(game.coins));
  if (coins.textContent !== value) {
    coins.textContent = value;
    coins.parentElement.animate([{ transform: "scale(1.18)" }, { transform: "scale(1)" }],
      { duration: 220 });
  }
  $("#hud-served").textContent = String(game.served);
  const combo = $("#hud-combo");
  combo.hidden = game.comboLevel() < 2;
  combo.textContent = `Combo x${game.comboLevel()}`;
  $("#hud-day").textContent = `Day ${game.day}`;
  $("#hud-clock").textContent = game.clock();
  const rep = $("#hud-rep");
  rep.style.width = `${Math.max(0, Math.min(100, game.rep))}%`;
  rep.dataset.level = game.rep < 25 ? "low" : game.rep < 50 ? "mid" : "high";
  $("#day-sun").style.left = `${Math.min(100, (game.t / SHIFT_SECONDS) * 100)}%`;
  const p95 = $("#hud-p95");
  p95.parentElement.dataset.blind = String(blind);
  p95.textContent = blind ? "?" : game.waits.length
    ? `${nearestRank(game.waits.slice(-20), 95).toFixed(1)}s` : "--";
}
