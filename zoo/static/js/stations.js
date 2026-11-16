import { api } from "./api.js";
import { critterCanvas } from "./art.js";
import { el } from "./dom.js";
import { renderMarkdown } from "./markdown.js";
import { CLASSIC } from "./mode.js";
import { SYSTEMS } from "./systems.js";

const LABEL = {
  healthy: "Online", broken: "Buggy", todo: "To build", checking: "Testing", unknown: "...",
};
const HARD_LABEL = { ...LABEL, healthy: "Shipped", todo: "Open" };
const $ = (selector, root = document) => root.querySelector(selector);

/**
 * The Stations tab: one card per level, and a drawer with what the level is about. Classic
 * stations replay their scene and list their TODOs. Hard mode stations show the ticket, its
 * acceptance tests and whether its block is placed on the blueprint.
 */
export class Stations {
  constructor(levels, mode, { onOpenBlueprint }) {
    this.levels = levels;
    this.mode = mode;
    this.hard = mode.key !== CLASSIC;
    this.labels = this.hard ? HARD_LABEL : LABEL;
    this.onOpenBlueprint = onOpenBlueprint;
    this.results = new Map();
    this.systems = {};
    this.openId = null;
    if (this.hard) {
      $("#stations-title").textContent = `${mode.title}: ten tickets`;
      $("#stations-lede").textContent = "Each ticket is a real incident in the project at "
        + `${mode.project}. No TODO marks the spot: read the ticket, find where the code goes, `
        + "make its acceptance tests pass, and place its block on the Blueprint.";
      $("#drawer-classic").hidden = true;
      $("#drawer-hard").hidden = false;
    }
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
        el("span", { class: "chip", "data-status": "unknown", text: this.labels.unknown }),
      ]),
      el("div", { class: "card-pattern", text: level.pattern }),
      el("div", { class: "card-station",
        text: this.hard ? level.title : `${level.station} / ${level.keeper}` }),
      el("div", { class: "card-headline", text: system.without }),
    ]);
    card.addEventListener("click", () => this.open(level.id));
    return card;
  }

  /** Statuses from the game's systems check, without replaying every scene. */
  update(systems) {
    this.systems = systems;
    for (const [id, system] of Object.entries(systems)) {
      const card = $(`.card[data-level="${id}"]`);
      if (!card) continue;
      card.dataset.status = system.status;
      const chip = $(".chip", card);
      chip.dataset.status = system.status;
      chip.textContent = this.labels[system.status] || system.status;
      $(".card-headline", card).textContent =
        system.status === "healthy" ? SYSTEMS[id].with : system.headline;
    }
    const online = Object.values(systems).filter((s) => s.status === "healthy").length;
    $("#stations-count").textContent = `${online}/${this.levels.length}`;
    if (this.hard && this.openId) this.render(this.openId);
  }

  open(id) {
    this.openId = id;
    $("#drawer").setAttribute("aria-hidden", "false");
    this.render(id);
    $(".drawer-close").focus();
    if (!this.hard) this.play(id);
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

  renderHead(level, status, headline) {
    const system = SYSTEMS[level.id];
    $(".drawer-panel").style.setProperty("--chip", system.color);
    $("#drawer-sprite").replaceChildren(critterCanvas(system.keeper, 104));
    $("#drawer-title").textContent = level.pattern;
    const chip = $("#drawer-chip");
    chip.dataset.status = status;
    chip.textContent = this.labels[status] || status;
    $("#drawer-headline").textContent = headline;
    $("#drawer-game").replaceChildren(
      el("p", { "data-kind": "without" }, [el("b", { text: "Not built" }),
        document.createTextNode(system.without)]),
      el("p", { "data-kind": "with" }, [el("b", { text: "Built" }),
        document.createTextNode(system.with)]),
    );
  }

  render(id) {
    if (this.hard) this.renderTicket(id);
    else this.renderStation(id);
  }

  renderStation(id) {
    const level = this.levels.find((item) => item.id === id);
    const result = this.results.get(id);
    this.renderHead(level, result ? result.status : "unknown", result ? result.headline : "");
    $("#drawer-eyebrow").textContent = `Station ${level.id} / ${level.station}`;
    $("#drawer-pitch").textContent = level.pitch;
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

  renderTicket(id) {
    const level = this.levels.find((item) => item.id === id);
    const system = this.systems[id] || { status: "unknown", headline: "", results: [] };
    this.renderHead(level, system.status, system.headline);
    $("#drawer-eyebrow").textContent = `Ticket ${level.id} / ${level.label}`;
    $("#drawer-pitch").textContent = level.title;

    const gate = $("#drawer-gate");
    if (system.placed) {
      gate.dataset.state = "open";
      gate.replaceChildren(el("p", { text: `Block ${id} is placed on the blueprint.` }));
    } else {
      const button = el("button", { class: "button", type: "button", text: "Open the Blueprint" });
      button.addEventListener("click", () => {
        this.close();
        this.onOpenBlueprint();
      });
      gate.dataset.state = "closed";
      gate.replaceChildren(
        el("p", { text: `Architecture first. Place block ${id} where it belongs on the `
          + "blueprint and link it to the components it talks to. The ticket ships only then." }),
        button,
      );
    }

    const results = system.results || [];
    $("#drawer-tests").replaceChildren(...(results.length ? results.map((result) =>
      el("li", { "data-outcome": result.outcome }, [
        el("span", { class: "test-name", text: result.name }),
        result.message ? el("span", { class: "test-message", text: result.message }) : "",
      ])) : [el("li", { "data-outcome": "pending",
      text: system.status === "checking" ? "Running..." : "No result yet" })]));

    $("#drawer-hard-command").textContent =
      `python -m zoo test --mode ${this.mode.key} ${level.number}\n`
      + `python -m zoo test --mode ${this.mode.key} ${level.number} -v`;
    $("#drawer-ticket").replaceChildren(
      el("p", { class: "ticket-path", text: `${this.mode.key}/${level.ticket}` }),
      renderMarkdown(level.ticket_text),
    );
  }
}
