/**
 * The Blueprint tab of the hard modes. The architecture of the project is drawn as boxes and
 * arrows with empty places. The player drags one block per pattern onto the place where it
 * belongs, links it to the components it talks to, then asks the server to check the design.
 * The answers never reach the page: only verdicts and hints come back.
 */
import { api } from "./api.js";
import { el } from "./game.js";
import { SYSTEMS } from "./systems.js";

const SVG_NS = "http://www.w3.org/2000/svg";
const BOX_W = 124;
const BOX_H = 44;
const DRAG_THRESHOLD = 5;
const VERDICT_TEXT = {
  correct: "Right place, right links.",
  wrong_place: "This is not where it belongs.",
  wrong_links: "Right place, but it does not talk to the right components.",
  unplaced: "Not on the diagram yet.",
};

function svg(tag, attributes = {}, children = []) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
  node.append(...children);
  return node;
}

/** Up to two lines of about `width` characters, the last one cut with an ellipsis. */
function wrap(label, width) {
  const lines = [""];
  for (const word of label.split(" ")) {
    const line = lines[lines.length - 1];
    if (!line) lines[lines.length - 1] = word;
    else if (`${line} ${word}`.length <= width) lines[lines.length - 1] = `${line} ${word}`;
    else lines.push(word);
  }
  if (lines.length > 2) lines.splice(2, lines.length, `${lines[1].slice(0, width - 1)}.`);
  return lines.slice(0, 2);
}

function boxText(x, y, label, className, width = 17) {
  const lines = wrap(label, width);
  const top = y + BOX_H / 2 - (lines.length - 1) * 7;
  return svg("text", { class: className, x: x + BOX_W / 2, y: top, "text-anchor": "middle",
    "dominant-baseline": "middle" },
  lines.map((line, i) => svg("tspan", { x: x + BOX_W / 2, dy: i ? 14 : 0 }, [line])));
}

const center = (item) => ({ x: item.x + BOX_W / 2, y: item.y + BOX_H / 2 });

export class BlueprintEditor {
  constructor(root, { onChecked }) {
    this.root = root;
    this.onChecked = onChecked;
    this.data = null;
    this.placements = {};
    this.checks = {};
    this.selected = null;
    this.busy = false;
    this.message = "";
  }

  async load() {
    const { blueprint, progress } = await api.blueprint();
    this.data = blueprint;
    this.components = Object.fromEntries(blueprint.components.map((item) => [item.id, item]));
    this.slots = Object.fromEntries(blueprint.slots.map((item) => [item.id, item]));
    this.applyProgress(progress);
    this.render();
    return progress;
  }

  applyProgress(progress) {
    this.placements = {};
    for (const [level, placement] of Object.entries(progress.placements || {})) {
      this.placements[level] = { slot: placement.slot, links: [...placement.links] };
    }
    this.checks = progress.checks || {};
  }

  /* Edits */

  blockAt(slot) {
    return Object.keys(this.placements).find((level) => this.placements[level].slot === slot);
  }

  place(level, slot) {
    const current = this.placements[level] || { slot: null, links: [] };
    const occupant = this.blockAt(slot);
    if (occupant && occupant !== level) {
      if (current.slot) this.placements[occupant].slot = current.slot;
      else delete this.placements[occupant];
      delete this.checks[occupant];
    }
    this.placements[level] = { slot, links: current.links };
    delete this.checks[level];
    this.selected = level;
    this.render();
  }

  unplace(level) {
    delete this.placements[level];
    delete this.checks[level];
    if (this.selected === level) this.selected = null;
    this.render();
  }

  toggleLink(component) {
    const placement = this.placements[this.selected];
    if (!placement?.slot) return;
    const links = new Set(placement.links);
    if (links.has(component)) links.delete(component);
    else links.add(component);
    placement.links = [...links];
    delete this.checks[this.selected];
    this.render();
  }

  select(level) {
    this.selected = this.selected === level ? null : level;
    this.render();
  }

  clear() {
    this.placements = {};
    this.checks = {};
    this.selected = null;
    this.message = "";
    this.render();
  }

  async check() {
    if (this.busy) return;
    this.busy = true;
    this.message = "Checking the design...";
    this.render();
    try {
      const progress = await api.checkBlueprint(this.placements);
      this.applyProgress(progress);
      this.message = progress.correct === progress.total
        ? "The architecture is complete. Every pattern sits where it belongs."
        : `${progress.correct} of ${progress.total} blocks are right. Read the hints below.`;
      this.onChecked(progress);
    } catch (error) {
      this.message = `The check failed: ${error.message}`;
    } finally {
      this.busy = false;
      this.render();
    }
  }

  /* Drag and drop: a press that moves is a drag, a press that does not is a click. */

  startDrag(event, level) {
    if (event.button !== 0) return;
    event.preventDefault();
    const origin = { x: event.clientX, y: event.clientY };
    const fromSlot = this.placements[level]?.slot || null;
    let ghost = null;
    let hovered = null;

    const targetAt = (x, y) => document.elementFromPoint(x, y)?.closest("[data-drop]");
    const move = (moveEvent) => {
      if (!ghost && Math.hypot(moveEvent.clientX - origin.x, moveEvent.clientY - origin.y)
        < DRAG_THRESHOLD) return;
      if (!ghost) {
        const block = this.data.blocks.find((item) => item.level === level);
        ghost = el("div", { class: "bp-ghost", style: `--chip:${SYSTEMS[level].color}` }, [
          el("b", { text: level }), document.createTextNode(block.label)]);
        document.body.append(ghost);
      }
      ghost.style.transform = `translate(${moveEvent.clientX + 8}px, ${moveEvent.clientY + 8}px)`;
      ghost.hidden = true;
      const target = targetAt(moveEvent.clientX, moveEvent.clientY);
      ghost.hidden = false;
      if (hovered !== target) {
        hovered?.classList.remove("bp-hover");
        target?.classList.add("bp-hover");
        hovered = target;
      }
    };
    const up = (upEvent) => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
      hovered?.classList.remove("bp-hover");
      if (!ghost) {
        this.select(level);
        return;
      }
      ghost.remove();
      const target = targetAt(upEvent.clientX, upEvent.clientY);
      if (target?.dataset.drop === "palette" && fromSlot) this.unplace(level);
      else if (target?.dataset.drop && target.dataset.drop !== "palette") this.place(level, target.dataset.drop);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  }

  /* Rendering */

  render() {
    if (!this.data) return;
    const placedCount = Object.values(this.placements).filter((item) => item.slot).length;
    const correct = Object.values(this.checks).filter((item) => item.verdict === "correct").length;
    const header = el("div", { class: "bp-head" }, [
      el("div", {}, [
        el("p", { class: "eyebrow", text: "Architecture first" }),
        el("h1", { text: `${this.data.title} blueprint` }),
        el("p", { class: "lede", text: this.data.intro }),
      ]),
      el("div", { class: "bp-score" }, [
        el("span", { class: "bp-score-value", text: `${correct}/${this.data.blocks.length}` }),
        el("span", { text: "blocks verified" }),
      ]),
    ]);
    const actions = el("div", { class: "bp-actions" }, [
      this.button("Check the design", () => this.check(), "button-primary", this.busy || !placedCount),
      this.button("Clear", () => this.clear(), "", this.busy),
      el("p", { class: "bp-message", "aria-live": "polite", text: this.message }),
    ]);
    this.root.replaceChildren(header, actions, el("div", { class: "bp-body" }, [
      this.palette(), el("div", { class: "bp-canvas" }, [this.selectionBar(), this.diagram()]),
    ]), this.report());
  }

  button(label, action, style, disabled) {
    const button = el("button", { class: `button ${style}`, type: "button", text: label });
    button.disabled = disabled;
    button.addEventListener("click", action);
    return button;
  }

  palette() {
    const waiting = this.data.blocks.filter((block) => !this.placements[block.level]?.slot);
    return el("div", { class: "bp-palette", "data-drop": "palette" }, [
      el("h2", { text: "Pattern blocks" }),
      el("p", { class: "muted", text: waiting.length
        ? "Drag a block onto a dashed place, or click it, then click a place."
        : "Every block is on the diagram. Drag one back here to remove it." }),
      ...waiting.map((block) => {
        const card = el("button", {
          class: "bp-block", type: "button", style: `--chip:${SYSTEMS[block.level].color}`,
          "aria-pressed": String(this.selected === block.level),
        }, [
          el("span", { class: "bp-block-title" }, [el("b", { text: block.level }),
            document.createTextNode(block.label)]),
          el("span", { class: "bp-block-blurb", text: block.blurb }),
        ]);
        card.addEventListener("pointerdown", (event) => this.startDrag(event, block.level));
        card.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            this.select(block.level);
          }
        });
        return card;
      }),
    ]);
  }

  selectionBar() {
    const level = this.selected;
    if (!level) {
      return el("p", { class: "bp-selection", text: "Select a placed block to link it to "
        + "components. Grey arrows are what the system does today." });
    }
    const block = this.data.blocks.find((item) => item.level === level);
    const placement = this.placements[level];
    const children = [el("span", { class: "pattern-chip", style: `--chip:${SYSTEMS[level].color}` },
      [el("b", { text: level }), document.createTextNode(block.label)])];
    if (placement?.slot) {
      children.push(document.createTextNode(
        ` Click components to link or unlink them (${placement.links.length} linked). `));
      children.push(this.button("Remove from the diagram", () => this.unplace(level), "button-small", false));
    } else {
      children.push(document.createTextNode(" Now click a dashed place on the diagram."));
    }
    return el("div", { class: "bp-selection", "data-active": "true" }, children);
  }

  diagram() {
    const { width, height } = this.data;
    const root = svg("svg", { viewBox: `0 0 ${width} ${height}`, class: "bp-svg",
      role: "img", "aria-label": `${this.data.title} architecture` });
    const edges = svg("g", { class: "bp-edges" });
    for (const [from, to] of this.data.edges) {
      const a = center(this.components[from]);
      const b = center(this.components[to]);
      edges.append(svg("line", { x1: a.x, y1: a.y, x2: b.x, y2: b.y }));
    }
    const links = svg("g", { class: "bp-links" });
    for (const [level, placement] of Object.entries(this.placements)) {
      if (!placement.slot) continue;
      const a = center(this.slots[placement.slot]);
      for (const component of placement.links) {
        const b = center(this.components[component]);
        links.append(svg("line", { x1: a.x, y1: a.y, x2: b.x, y2: b.y,
          style: `--chip:${SYSTEMS[level].color}`,
          "data-selected": String(level === this.selected) }));
      }
    }
    root.append(edges, links);

    const linked = new Set(this.selected ? this.placements[this.selected]?.links || [] : []);
    for (const item of this.data.components) {
      const group = svg("g", { class: "bp-component", "data-kind": item.kind,
        "data-linkable": String(Boolean(this.placements[this.selected]?.slot)),
        "data-linked": String(linked.has(item.id)) }, [
        svg("rect", { x: item.x, y: item.y, width: BOX_W, height: BOX_H, rx: 10 }),
        boxText(item.x, item.y, item.label, "bp-label"),
      ]);
      group.addEventListener("click", () => this.toggleLink(item.id));
      root.append(group);
    }

    for (const slot of this.data.slots) {
      const level = this.blockAt(slot.id);
      if (!level) {
        const group = svg("g", { class: "bp-slot", "data-drop": slot.id }, [
          svg("rect", { x: slot.x, y: slot.y, width: BOX_W, height: BOX_H, rx: 10 }),
          svg("text", { x: slot.x + BOX_W / 2, y: slot.y + BOX_H / 2, "text-anchor": "middle",
            "dominant-baseline": "middle", class: "bp-slot-mark" }, ["?"]),
        ]);
        group.addEventListener("click", () => {
          if (this.selected) this.place(this.selected, slot.id);
        });
        root.append(group);
        continue;
      }
      const block = this.data.blocks.find((item) => item.level === level);
      const verdict = this.checks[level]?.verdict || "unchecked";
      const group = svg("g", { class: "bp-placed", "data-drop": slot.id,
        "data-verdict": verdict, "data-selected": String(level === this.selected),
        style: `--chip:${SYSTEMS[level].color}` }, [
        svg("rect", { x: slot.x, y: slot.y, width: BOX_W, height: BOX_H, rx: 10 }),
        boxText(slot.x, slot.y, `${level} ${block.label}`, "bp-label bp-label-block", 18),
      ]);
      group.addEventListener("pointerdown", (event) => this.startDrag(event, level));
      root.append(group);
    }
    return root;
  }

  report() {
    const checked = Object.keys(this.checks).length > 0;
    if (!checked) return el("div", { class: "bp-report", hidden: "" });
    return el("ol", { class: "bp-report" }, this.data.blocks.map((block) => {
      const check = this.checks[block.level];
      const verdict = check?.verdict || "unchecked";
      const parts = [
        el("span", { class: "pattern-chip", style: `--chip:${SYSTEMS[block.level].color}` },
          [el("b", { text: block.level }), document.createTextNode(block.label)]),
        el("span", { class: "bp-verdict", text: check ? VERDICT_TEXT[verdict]
          : "Changed since the last check." }),
      ];
      if (verdict === "wrong_links") {
        const counts = [];
        if (check.missing) counts.push(`${check.missing} link${check.missing > 1 ? "s" : ""} missing`);
        if (check.extra) counts.push(`${check.extra} link${check.extra > 1 ? "s" : ""} too many`);
        parts.push(el("span", { class: "bp-detail", text: counts.join(", ") }));
      }
      if (check?.hint) parts.push(el("span", { class: "bp-hint", text: `Hint: ${check.hint}` }));
      return el("li", { "data-verdict": verdict }, parts);
    }));
  }
}
