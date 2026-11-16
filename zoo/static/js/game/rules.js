/** The rules of a shift: timings, prices and thresholds, the animals and the incidents. */

export const SHIFT_SECONDS = 180;
export const PATIENCE = 30;
export const HUNGRY_AT = 25;
export const TICK_MS = 100;
export const START_COINS = 20;
export const START_REP = 70;
export const MAX_QUEUE = 6;
export const HUNGER_DECAY = 1.0;
export const HUNGER_PER_GRAM = 0.8;
export const STUFFED_AT = 125;
export const SICK_SECONDS = 12;
export const DB_LAG_MS = 1000;
export const PAGER_LEAD = 5;
export const STORM_SECONDS = 25;
export const DIRT_EVERY = 15;
export const ADOPTION_WINDOW = 16;
export const STAR_SCORES = [150, 350, 550];
export const BEST_KEY = "zoo-ops-best-score";
export const DAY_KEY = "zoo-ops-day";
export const MAX_TASKS = 4;

export const ANIMALS = [
  { id: "lion", name: "Leo", kind: "lion" },
  { id: "otter", name: "Pebble", kind: "otter" },
  { id: "penguin", name: "Waddle", kind: "penguin" },
  { id: "miso", name: "Miso", kind: "cat" },
];
export const VISITOR_KINDS = ["hedgehog", "rabbit", "frog"];
export const INCIDENTS = [
  { at: 40, kind: "pigeons", label: "Pigeons", soon: "a pigeon swarm is coming" },
  { at: 72, kind: "storm", label: "Storm", soon: "a storm is coming" },
  { at: 108, kind: "raccoon", label: "Intruder", soon: "someone is at the staff door" },
  { at: 135, kind: "release", label: "Release", soon: "kiosk v2 is rolling out" },
];
export const ADOPTIONS = [28, 88, 150];
export const NOTE_SYSTEMS = [
  [/cache/i, "01"],
  [/fallback|never answered|every model|kiosk code/i, "03"],
  [/idempotency|unique|food bowl/i, "04"],
  [/sse/i, "08"],
];
