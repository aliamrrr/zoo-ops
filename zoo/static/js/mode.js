/**
 * Which Zoo Ops is being played: classic, hard or hardpp. The mode comes from the address
 * (?mode=hard), then from the last mode played, and every saved value is kept per mode.
 */
const MODE_KEY = "zoo-ops-mode";
export const CLASSIC = "classic";

function stored() {
  try {
    return localStorage.getItem(MODE_KEY);
  } catch {
    return null;
  }
}

function remember(key) {
  try {
    localStorage.setItem(MODE_KEY, key);
  } catch {
    /* private mode: the address still carries the mode */
  }
}

export function readMode(knownKeys) {
  const fromUrl = new URLSearchParams(window.location.search).get("mode");
  const key = [fromUrl, stored()].find((candidate) => knownKeys.includes(candidate)) || CLASSIC;
  remember(key);
  return key;
}

export function switchMode(key) {
  remember(key);
  const url = new URL(window.location.href);
  url.searchParams.set("mode", key);
  window.location.assign(url);
}

/** Classic keeps its historical storage keys, the other modes get their own. */
export function scopedKey(base, mode) {
  return mode === CLASSIC ? base : `${base}:${mode}`;
}
