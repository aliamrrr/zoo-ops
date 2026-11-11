/**
 * The ten backend systems: what each one is called, who keeps it, and what it changes in
 * the game. One entry per level id. Everything the game shows about a pattern comes from here.
 */
export const SYSTEMS = {
  "01": {
    label: "Cache",
    name: "nut store",
    keeper: "squirrel",
    color: "#d9822b",
    without: "Every question goes to the Owl: 3 coins and a long wait each time.",
    with: "Repeated questions come straight from Hazel's nut store: instant and free.",
  },
  "02": {
    label: "Rate limit",
    name: "gate limiter",
    keeper: "goose",
    color: "#2f8fd6",
    without: "The pigeon swarm reaches the Owl, jams the kiosk and runs up the bill.",
    with: "Gus throttles the pigeons per key, the kiosk keeps serving visitors.",
  },
  "03": {
    label: "Reliability",
    name: "bridge",
    keeper: "fox",
    color: "#e2603a",
    without: "During the storm every question hangs on the dead Owl, then fails.",
    with: "Rusty retries, opens the breaker and falls back to the Parrot.",
  },
  "04": {
    label: "Idempotency",
    name: "kitchen",
    keeper: "cat",
    color: "#7a62d9",
    without: "Lost responses make the client retry, and every retry feeds the animal again.",
    with: "Each order is served once, retries get the stored response.",
  },
  "05": {
    label: "Observability",
    name: "lookout",
    keeper: "meerkat",
    color: "#159e8c",
    without: "No telemetry: hunger and patience bars are hidden, no forecast, no pager.",
    with: "Bars, wait p95, the incident forecast and a pager warning before each incident.",
  },
  "06": {
    label: "DB speed",
    name: "burrows",
    keeper: "mole",
    color: "#8a6a4a",
    without: "Slow queries: every action you take lags by a second.",
    with: "Indexed, paginated, pooled: actions are instant.",
  },
  "07": {
    label: "Integrity",
    name: "adoption office",
    keeper: "beaver",
    color: "#d9538a",
    without: "Two families racing for the same kitten both take it home.",
    with: "Optimistic locking: one family gets the kitten, the other a polite no.",
  },
  "08": {
    label: "Async",
    name: "anthill",
    keeper: "ant",
    color: "#b0483f",
    without: "Answers arrive all at once after a silent wait, and you clean every pen by hand.",
    with: "The Owl streams word by word, and the ants clean dirty pens in the background.",
  },
  "09": {
    label: "Auth",
    name: "kennel",
    keeper: "dog",
    color: "#3f5fae",
    without: "The raccoon walks in with a forged badge and steals coins.",
    with: "Rex checks every badge and tenant: the raccoon leaves empty-handed.",
  },
  "10": {
    label: "Deploy",
    name: "nest",
    keeper: "canary",
    color: "#6c9a1f",
    without: "The bad v2 release breaks the kiosk for everyone, closing drops the line.",
    with: "The canary catches v2 and rolls it back, closing drains the line.",
  },
};

export const SYSTEM_IDS = Object.keys(SYSTEMS).sort();
