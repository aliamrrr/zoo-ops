/** Small helpers of the shift: time, chance, percentiles and numbers kept between visits. */

export const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
export const random = (min, max) => min + Math.random() * (max - min);
export const pick = (items) => items[Math.floor(Math.random() * items.length)];

/** The p-th percentile by nearest rank, the way the Lookout reports wait times. */
export function nearestRank(values, p) {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.max(0, Math.ceil((p / 100) * sorted.length) - 1)];
}

export function readNumber(key, fallback) {
  try {
    return Number(localStorage.getItem(key)) || fallback;
  } catch {
    return fallback;
  }
}

export function writeNumber(key, value) {
  try {
    localStorage.setItem(key, String(value));
  } catch {
    /* private mode: progress is simply not remembered */
  }
}
