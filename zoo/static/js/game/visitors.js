/** Visitors: they arrive, wait, give up, and hear the Owl's answer (or its failure). */
import { pick } from "./helpers.js";
import { MAX_QUEUE, NOTE_SYSTEMS, PATIENCE, VISITOR_KINDS } from "./rules.js";

export function spawnVisitor(game) {
  const waiting = game.visitors.filter((visitor) => visitor.state === "waiting");
  if (waiting.length >= MAX_QUEUE) {
    game.hurt(game.online("01") ? null : "01", 1);
    game.lost += 1;
    game.say("goose", "The line is full!", 2);
    return;
  }
  const [topic, question] = pick(game.questions);
  const vip = game.t > 15 && Math.random() < 0.14;
  const patience = vip ? PATIENCE * 0.6 : PATIENCE;
  game.visitors.push({
    id: game.nextId++, kind: pick(VISITOR_KINDS), topic, question, vip,
    patience, maxPatience: patience, state: "waiting", engaged: false, gone: false,
    arrivedAt: game.t,
  });
}

export function removeVisitor(game, visitor, happy) {
  visitor.gone = true;
  game.visitors = game.visitors.filter((item) => item !== visitor);
  game.departures.push({ id: visitor.id, kind: visitor.kind, happy, at: game.t });
  game.sfx(happy ? "coin" : "angry");
}

export function visitorGivesUp(game, visitor) {
  let blame = null;
  if (visitor.state === "asking") {
    if (game.t < game.stormUntil && !game.online("03")) blame = "03";
    else if (!game.online("08")) blame = "08";
  } else if (!game.online("01")) {
    blame = "01";
  }
  game.lost += 1;
  game.combo = 0;
  game.hurt(blame, 6);
  const why = visitor.state === "asking" ? "waited for an answer too long" : "waited in line too long";
  game.log(`A visitor ${why} and left angry.`, "bad", blame);
  removeVisitor(game, visitor, false);
}

export function answerFails(game, visitor, reason, blame) {
  game.speech = { text: reason, state: "error" };
  if (visitor.gone) return;
  game.lost += 1;
  game.combo = 0;
  game.hurt(blame, 6);
  game.log(`${reason} The visitor left angry.`, "bad", blame);
  removeVisitor(game, visitor, false);
}

export function onMeta(game, meta, visitor) {
  if (meta.failed) return;
  if (meta.cost) game.earn(-meta.cost, "kiosk");
  game.trip = { ...game.trip, provider: meta.provider };
  if (meta.provider === "cache") {
    game.emit("01", true, "Cache hit: instant answer, 0 coins");
    game.fx("toss", { visitor: visitor.id });
  } else if (!game.online("01") && game.askedTopics.has(visitor.topic)) {
    game.emit("01", false, "No cache: same question, paid twice", null, 7);
  }
  if (meta.provider === "parrot") {
    game.sfx("squawk");
    game.say("parrot", "Squawk! I got game!", 2.5);
    game.emit("03", true, meta.sim_seconds < 2 ? "Circuit open: skip the Owl, ask the Parrot"
      : "Owl down: retry, then the Parrot answers");
  }
  if (meta.streamed) {
    game.emit("08", true, "Streaming: words arrive live", "kiosk", 30);
  } else if (meta.provider !== "cache") {
    game.emit("08", false, "No streaming: long silent wait", "kiosk", 30);
  }
}

export function noteOnce(game, note) {
  if (game.notes.has(note)) return;
  game.notes.add(note);
  const match = NOTE_SYSTEMS.find(([pattern]) => pattern.test(note));
  game.log(`Backend: ${note}.`, "warn", match ? match[1] : null);
}
