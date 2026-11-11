/**
 * The pattern dock: one badge per system design pattern, under the zoo. A badge shows who
 * keeps the pattern, whether it is built, and flashes each time the pattern acts in the game.
 */
import { critterCanvas, paintCritterCanvas } from "./art.js";
import { el } from "./game.js";
import { SYSTEMS, SYSTEM_IDS } from "./systems.js";

export class Dock {
  constructor(root, onOpen) {
    this.badges = {};
    for (const id of SYSTEM_IDS) {
      const system = SYSTEMS[id];
      const face = critterCanvas(system.keeper, 46, { face: true, eyes: "asleep" });
      const good = el("span", { class: "tally tally-good", title: "Times it helped this shift" });
      const bad = el("span", { class: "tally tally-bad", title: "Times its absence hurt this shift" });
      const state = el("span", { class: "badge-state", text: "checking" });
      const effect = el("span", { class: "badge-effect" });
      const node = el("button", { class: "badge", type: "button", "data-built": "unknown",
        style: `--chip:${system.color}` }, [
        el("span", { class: "badge-face" }, [face, el("b", { text: id })]),
        el("span", { class: "badge-text" }, [
          el("span", { class: "badge-name", text: system.label }),
          el("span", { class: "badge-line" }, [state, good, bad]),
        ]),
        el("span", { class: "badge-card", role: "tooltip" }, [
          el("strong", { text: `${id} ${system.label}` }),
          effect,
          el("em", { text: "Click to open the station" }),
        ]),
      ]);
      node.addEventListener("click", () => onOpen(id));
      this.badges[id] = { node, face, good, bad, state, effect };
      root.append(node);
    }
  }

  update(systems) {
    for (const [id, badge] of Object.entries(this.badges)) {
      const built = systems[id]?.status === "healthy";
      const broken = systems[id]?.status === "broken";
      badge.node.dataset.built = String(built);
      badge.state.textContent = built ? "on duty" : broken ? "buggy" : "asleep";
      badge.effect.textContent = built ? SYSTEMS[id].with : SYSTEMS[id].without;
      paintCritterCanvas(badge.face, SYSTEMS[id].keeper, { face: true, eyes: built ? "open" : "asleep" });
    }
  }

  reset() {
    for (const badge of Object.values(this.badges)) {
      badge.good.textContent = "";
      badge.bad.textContent = "";
    }
  }

  pulse(id, good, stat) {
    const badge = this.badges[id];
    badge.good.textContent = stat.good ? `+${stat.good}` : "";
    badge.bad.textContent = stat.bad ? `-${stat.bad}` : "";
    badge.node.animate(good
      ? [{ transform: "translateY(0) scale(1)" }, { transform: "translateY(-10px) scale(1.08)" },
        { transform: "translateY(0) scale(1)" }]
      : [{ transform: "translateX(0)" }, { transform: "translateX(-5px)" },
        { transform: "translateX(5px)" }, { transform: "translateX(0)" }],
    { duration: good ? 420 : 320 });
    badge.node.dataset.flash = good ? "good" : "bad";
    clearTimeout(badge.timer);
    badge.timer = setTimeout(() => {
      delete badge.node.dataset.flash;
    }, 900);
  }
}
