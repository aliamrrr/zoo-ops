/** Particles, floating numbers and screen shake: the juice on top of the world. */
import { coin, heart, oval, sparkle, text } from "./art.js";

const CONFETTI = ["#ff8fab", "#ffd23f", "#6cc5f2", "#8f7ae6", "#7fd06c", "#ffffff"];

const KINDS = {
  heart: { speed: 40, gravity: -30, life: 1.1, size: 7 },
  spark: { speed: 90, gravity: 0, life: 0.7, size: 7 },
  puff: { speed: 40, gravity: -20, life: 0.6, size: 9 },
  coin: { speed: 150, gravity: 420, life: 0.9, size: 6 },
  crumb: { speed: 90, gravity: 380, life: 0.5, size: 3 },
  splash: { speed: 150, gravity: 460, life: 0.6, size: 4 },
  dirt: { speed: 110, gravity: 380, life: 0.5, size: 4 },
  confetti: { speed: 260, gravity: 220, life: 2.6, size: 6 },
};

export class Fx {
  constructor() {
    this.parts = [];
    this.pops = [];
    this.shake = 0;
  }

  burst(kind, x, y, count = 8, color = null) {
    const spec = KINDS[kind];
    for (let i = 0; i < count; i += 1) {
      const angle = kind === "confetti" || kind === "coin" || kind === "splash"
        ? -Math.PI / 2 + (Math.random() - 0.5) * 1.9
        : Math.random() * Math.PI * 2;
      const speed = spec.speed * (0.5 + Math.random() * 0.8);
      this.parts.push({
        kind, x, y, vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed,
        gravity: spec.gravity, life: spec.life * (0.7 + Math.random() * 0.5), age: 0,
        size: spec.size * (0.7 + Math.random() * 0.6), spin: Math.random() * 6,
        color: color || (kind === "confetti" ? CONFETTI[i % CONFETTI.length] : null),
      });
    }
  }

  pop(value, x, y, color = "#ffffff", size = 20) {
    this.pops.push({ value, x, y, color, size, age: 0 });
  }

  update(dt) {
    this.shake = Math.max(0, this.shake - dt * 14);
    for (const part of this.parts) {
      part.age += dt;
      part.vy += part.gravity * dt;
      part.x += part.vx * dt;
      part.y += part.vy * dt;
    }
    this.parts = this.parts.filter((part) => part.age < part.life);
    for (const pop of this.pops) pop.age += dt;
    this.pops = this.pops.filter((pop) => pop.age < 1.3);
  }

  offset() {
    if (this.shake <= 0) return [0, 0];
    return [(Math.random() - 0.5) * this.shake, (Math.random() - 0.5) * this.shake];
  }

  draw(ctx) {
    for (const part of this.parts) {
      const k = part.age / part.life;
      ctx.globalAlpha = k > 0.7 ? (1 - k) / 0.3 : 1;
      const { x, y, size } = part;
      switch (part.kind) {
        case "heart":
          heart(ctx, x + Math.sin(part.age * 5 + part.spin) * 4, y, size, part.color || "#ff6b8f");
          break;
        case "spark":
          sparkle(ctx, x, y, size * (1 - k * 0.5), part.color || "#fff6b0");
          break;
        case "puff":
          oval(ctx, x, y, size * (0.6 + k), size * (0.6 + k), part.color || "rgba(255,255,255,0.85)");
          break;
        case "coin":
          coin(ctx, x, y, size);
          break;
        case "confetti":
          ctx.save();
          ctx.translate(x, y);
          ctx.rotate(part.spin + part.age * 7);
          ctx.fillStyle = part.color;
          ctx.fillRect(-size / 2, -size / 4, size, size / 2);
          ctx.restore();
          break;
        default:
          oval(ctx, x, y, size, size, part.color || (part.kind === "splash" ? "#bfe9ff" : "#b98a5e"));
      }
    }
    ctx.globalAlpha = 1;
    for (const pop of this.pops) {
      const rise = Math.min(1, pop.age / 0.25);
      const scale = pop.age < 0.18 ? 0.6 + (pop.age / 0.18) * 0.55 : 1.15 - Math.min(0.15, (pop.age - 0.18) * 1.5);
      ctx.globalAlpha = pop.age > 0.95 ? Math.max(0, (1.3 - pop.age) / 0.35) : 1;
      text(ctx, pop.value, pop.x, pop.y - 18 * rise - pop.age * 16,
        { size: pop.size * scale, color: pop.color, stroke: "#4b3757", weight: 800 });
    }
    ctx.globalAlpha = 1;
  }
}
