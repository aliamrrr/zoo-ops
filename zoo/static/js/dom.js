/** Building the page: a tiny element helper and the colored chip that names a pattern. */
import { SYSTEMS } from "./systems.js";

export const $ = (selector) => document.querySelector(selector);

export function el(tag, attributes = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attributes)) {
    if (key === "text") node.textContent = value;
    else node.setAttribute(key, value);
  }
  node.append(...children);
  return node;
}

/** The colored "04 Idempotency" tag used everywhere a pattern is named. */
export function patternChip(id, tag = "span") {
  const chip = el(tag, { class: "pattern-chip", style: `--chip:${SYSTEMS[id].color}` }, [
    el("b", { text: id }),
    document.createTextNode(SYSTEMS[id].label),
  ]);
  if (tag === "button") chip.type = "button";
  return chip;
}
