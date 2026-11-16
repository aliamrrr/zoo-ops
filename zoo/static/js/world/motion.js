/** Where the keepers stand, where the caution tape goes, and how things move between points. */
import { P } from "../scenery.js";

export const KEEPERS = [
  { id: "01", who: "squirrel", kind: "squirrel", spot: P.squirrel, size: 54 },
  { id: "02", who: "goose", kind: "goose", spot: P.goose, size: 58 },
  { id: "03", who: "fox", kind: "fox", spot: P.fox, size: 56 },
  { id: "05", who: "meerkat", kind: "meerkat", spot: P.meerkat, size: 54, perched: true },
  { id: "06", who: "mole", kind: "mole", spot: P.mole, size: 50 },
  { id: "07", who: "beaver", kind: "beaver", spot: P.beaver, size: 54 },
  { id: "09", who: "dog", kind: "dog", spot: P.dog, size: 56 },
  { id: "10", who: "canary", kind: "canary", spot: P.nest, size: 40, perched: true },
];

/** Where the caution tape goes while a system is not built. */
export const TAPES = {
  "01": [P.cache.x, P.cache.y - 4, 86],
  "02": [P.gate.x, P.gate.y - 34, 76],
  "03": [P.perch.x, P.perch.y + 54, 62],
  "04": [P.kitchen.x, P.kitchen.y - 20, 86],
  "05": [P.lookout.x, P.lookout.y - 12, 88],
  "06": [P.burrows.x, P.burrows.y + 14, 126],
  "07": [P.adoption.x, P.adoption.y - 6, 100],
  "08": [P.anthill.x, P.anthill.y - 4, 100],
  "09": [P.kennel.x, P.kennel.y - 4, 78],
  "10": [P.nestTree.x, P.nestTree.y - 26, 52],
};

export const lerp = (a, b, k) => a + (b - a) * k;
export const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
export const between = (a, b, k) => ({ x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k) });

export function moveToward(position, target, speed, dt) {
  const dx = target.x - position.x;
  const dy = target.y - position.y;
  const distance = Math.hypot(dx, dy);
  if (distance < 1) {
    position.x = target.x;
    position.y = target.y;
    return false;
  }
  const step = Math.min(distance, speed * dt);
  position.x += (dx / distance) * step;
  position.y += (dy / distance) * step;
  if (Math.abs(dx) > 0.5) position.flip = dx < 0;
  return dt > 0;
}

/** Follow a polyline of points at a 0..1 progress. */
export function along(points, k) {
  const scaled = clamp(k, 0, 1) * (points.length - 1);
  const index = Math.min(points.length - 2, Math.floor(scaled));
  return between(points[index], points[index + 1], scaled - index);
}

export const hop = (time, seed = 0) => Math.abs(Math.sin(time * 9 + seed)) * 5;
export const blinking = (time, seed) => (time + seed * 1.7) % 3.4 < 0.13;
