async function request(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) throw new Error(`${path} answered HTTP ${response.status}`);
  return response.json();
}

/** The server restarts when a level file is saved: retry once after it comes back. */
async function withRetry(call) {
  try {
    return await call();
  } catch {
    await new Promise((resolve) => setTimeout(resolve, 1500));
    return call();
  }
}

export const api = {
  levels: () => withRetry(() => request("/api/levels")),
  systems: () => withRetry(() => request("/api/game/systems")),
  questions: () => withRetry(() => request("/api/game/questions")),
  reset: () => withRetry(() => request("/api/game/reset", { method: "POST" })),
  playLevel: (id) => request(`/api/levels/${id}/play`, { method: "POST" }),
  feed: (animal) => withRetry(() =>
    request(`/api/game/feed?animal=${encodeURIComponent(animal)}`, { method: "POST" })),
  ask,
};

/** Parse one Server-Sent Event block, the way a browser does. */
function parseEvent(block) {
  const event = { event: "message", data: [] };
  for (const line of block.split("\n")) {
    if (!line || line.startsWith(":")) continue;
    const colon = line.indexOf(":");
    const field = colon === -1 ? line : line.slice(0, colon);
    let value = colon === -1 ? "" : line.slice(colon + 1);
    if (value.startsWith(" ")) value = value.slice(1);
    if (field === "data") event.data.push(value);
    else if (field === "event") event.event = value;
    else if (field === "id") event.id = value;
  }
  return { ...event, data: event.data.join("\n") };
}

/**
 * Ask the Owl. The server answers with an SSE stream when level 08 is built, or with plain
 * JSON after the whole wait otherwise. Returns the meta data plus how the answer arrived.
 */
async function ask(question, storm, { onMeta, onToken }) {
  const url = `/api/game/ask?q=${encodeURIComponent(question)}&storm=${storm}`;
  let response;
  try {
    response = await fetch(url);
  } catch {
    return { failed: true, notes: ["the kiosk server is restarting"] };
  }
  if (!response.ok) return { failed: true, notes: [`kiosk answered HTTP ${response.status}`] };

  if ((response.headers.get("content-type") || "").includes("application/json")) {
    const meta = await response.json();
    onMeta(meta);
    if (!meta.failed) onToken(meta.answer);
    return { ...meta, streamed: false };
  }

  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  let meta = null;
  let finished = false;
  let crash = null;
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value.replaceAll("\r\n", "\n");
    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const event = parseEvent(buffer.slice(0, boundary));
      buffer = buffer.slice(boundary + 2);
      boundary = buffer.indexOf("\n\n");
      if (event.event === "meta") {
        try {
          meta = JSON.parse(event.data);
          onMeta(meta);
        } catch {
          crash = "the meta event is not valid JSON";
        }
      } else if (event.event === "token") {
        onToken(event.data);
      } else if (event.event === "done") {
        finished = true;
      } else if (event.event === "crash") {
        crash = event.data;
      }
    }
  }
  if (!meta || !finished || crash) {
    return {
      ...(meta || {}),
      failed: true,
      garbled: true,
      streamed: true,
      notes: [crash || "the SSE stream could not be parsed: check sse_event()"],
    };
  }
  return { ...meta, streamed: true };
}
