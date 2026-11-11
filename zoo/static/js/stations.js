import { api } from "./api.js";
import { critterCanvas } from "./art.js";
import { el } from "./game.js";
import { SYSTEMS } from "./systems.js";

const LABEL = { healthy: "Online", broken: "Buggy", todo: "To build", unknown: "..." };
const $ = (selector, root = document) => root.querySelector(selector);

/** The Stations tab: one card per level, and a drawer with its scene, TODOs and commands. */
export class Stations {
  constructor(levels) {
    this.levels = levels;
    this.results = new Map();
    this.openId = null;
    $("#map").replaceChildren(...levels.map((level) => this.card(level)));
    document.querySelectorAll("[data-close]").forEach((node) =>
      node.addEventListener("click", () => this.close()));
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && this.openId) this.close();
    });
    $("#drawer-replay").addEventListener("click", () => this.openId && this.play(this.openId));
  }

  card(level) {
    const system = SYSTEMS[level.id];
    const card = el("button", {
      class: "card", type: "button", "data-level": level.id, "data-status": "unknown",
      style: `--chip:${system.color}`,
    }, [
      el("div", { class: "card-stage" }, [
        el("span", { class: "card-number", text: level.id }),
        critterCanvas(system.keeper, 96),
        el("span", { class: "chip", "data-status": "unknown", text: LABEL.unknown }),
      ]),
      el("div", { class: "card-pattern", text: level.pattern }),
      el("div", { class: "card-station", text: `${level.station} / ${level.keeper}` }),
      el("div", { class: "card-headline", text: system.without }),
    ]);
    card.addEventListener("click", () => this.open(level.id));
    return card;
  }

  /** Statuses from the game's systems check, without replaying every scene. */
  update(systems) {
    for (const [id, system] of Object.entries(systems)) {
      const card = $(`.card[data-level="${id}"]`);
      if (!card) continue;
      card.dataset.status = system.status;
      const chip = $(".chip", card);
      chip.dataset.status = system.status;
      chip.textContent = LABEL[system.status];
      $(".card-headline", card).textContent =
        system.status === "healthy" ? SYSTEMS[id].with : system.headline;
    }
    const online = Object.values(systems).filter((s) => s.status === "healthy").length;
    $("#stations-count").textContent = `${online}/${this.levels.length}`;
  }

  open(id) {
    this.openId = id;
    $("#drawer").setAttribute("aria-hidden", "false");
    this.render(id);
    $(".drawer-close").focus();
    this.play(id);
  }

  close() {
    const id = this.openId;
    this.openId = null;
    $("#drawer").setAttribute("aria-hidden", "true");
    if (id) $(`.card[data-level="${id}"]`)?.focus();
  }

  async play(id) {
    $("#drawer-headline").textContent = "Replaying the scene...";
    try {
      this.results.set(id, await api.playLevel(id));
    } catch (error) {
      this.results.set(id, {
        status: "broken", headline: error.message, events: [], metrics: {}, todos_left: [],
      });
    }
    if (this.openId === id) this.render(id);
  }

  render(id) {
    const level = this.levels.find((item) => item.id === id);
    const system = SYSTEMS[id];
    const result = this.results.get(id);
    $(".drawer-panel").style.setProperty("--chip", system.color);
    $("#drawer-sprite").replaceChildren(critterCanvas(system.keeper, 104));
    $("#drawer-eyebrow").textContent = `Station ${level.id} / ${level.station}`;
    $("#drawer-title").textContent = level.pattern;
    const chip = $("#drawer-chip");
    chip.dataset.status = result ? result.status : "unknown";
    chip.textContent = LABEL[result ? result.status : "unknown"];
    $("#drawer-pitch").textContent = level.pitch;
    $("#drawer-headline").textContent = result ? result.headline : "";
    $("#drawer-game").replaceChildren(
      el("p", { "data-kind": "without" }, [el("b", { text: "Not built" }), document.createTextNode(system.without)]),
      el("p", { "data-kind": "with" }, [el("b", { text: "Built" }), document.createTextNode(system.with)]),
    );
    $("#drawer-log").replaceChildren(...(result ? result.events : []).map((event) =>
      el("li", { "data-tone": event.tone, text: event.text })));
    $("#drawer-metrics").replaceChildren(...Object.entries(result ? result.metrics : {}).map(
      ([name, value]) => el("div", {}, [el("dt", { text: name }), el("dd", { text: value })])));
    const left = new Set(result ? result.todos_left : level.todos_left);
    $("#drawer-file").textContent = level.file;
    $("#drawer-todos").replaceChildren(...level.todos.map((todo) =>
      el("li", { "data-done": String(!left.has(todo)) }, [
        el("span", { text: todo }),
        el("span", { text: left.has(todo) ? "todo" : "written" }),
      ])));
    $("#drawer-command").textContent =
      `python -m zoo test ${level.number}\npython -m zoo scene ${level.number}`;
  }
}
