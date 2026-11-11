/** Tiny synthesized sound effects (Web Audio, no files). Muted state is remembered. */

const KEY = "zoo-ops-muted";

function readMuted() {
  try {
    return localStorage.getItem(KEY) === "1";
  } catch {
    return false;
  }
}

export class Sfx {
  constructor() {
    this.muted = readMuted();
    this.ctx = null;
  }

  toggle() {
    this.muted = !this.muted;
    try {
      localStorage.setItem(KEY, this.muted ? "1" : "0");
    } catch {
      /* private mode: the choice lasts for this page only */
    }
    return this.muted;
  }

  /** Browsers only allow audio after a user gesture: call this from a click. */
  unlock() {
    if (!this.ctx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) this.ctx = new AudioContext();
    }
    if (this.ctx && this.ctx.state === "suspended") this.ctx.resume();
  }

  tone(freq, duration, { type = "sine", gain = 0.08, slide = null, delay = 0 } = {}) {
    const start = this.ctx.currentTime + delay;
    const osc = this.ctx.createOscillator();
    const amp = this.ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, start);
    if (slide) osc.frequency.exponentialRampToValueAtTime(slide, start + duration);
    amp.gain.setValueAtTime(0.0001, start);
    amp.gain.exponentialRampToValueAtTime(gain, start + 0.012);
    amp.gain.exponentialRampToValueAtTime(0.0001, start + duration);
    osc.connect(amp).connect(this.ctx.destination);
    osc.start(start);
    osc.stop(start + duration + 0.02);
  }

  noise(duration, { gain = 0.08, cutoff = 1200, delay = 0 } = {}) {
    const start = this.ctx.currentTime + delay;
    const length = Math.ceil(this.ctx.sampleRate * duration);
    const buffer = this.ctx.createBuffer(1, length, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < length; i += 1) data[i] = (Math.random() * 2 - 1) * (1 - i / length);
    const source = this.ctx.createBufferSource();
    const filter = this.ctx.createBiquadFilter();
    const amp = this.ctx.createGain();
    source.buffer = buffer;
    filter.type = "lowpass";
    filter.frequency.value = cutoff;
    amp.gain.value = gain;
    source.connect(filter).connect(amp).connect(this.ctx.destination);
    source.start(start);
  }

  play(name) {
    if (this.muted || !this.ctx || this.ctx.state !== "running") return;
    switch (name) {
      case "pop":
        this.tone(520, 0.09, { slide: 900 });
        break;
      case "coin":
        this.tone(988, 0.07, { type: "square", gain: 0.04 });
        this.tone(1319, 0.16, { type: "square", gain: 0.04, delay: 0.07 });
        break;
      case "good":
        [660, 880, 1320].forEach((f, i) => this.tone(f, 0.12, { type: "triangle", delay: i * 0.07 }));
        break;
      case "bad":
        this.tone(220, 0.28, { type: "sawtooth", gain: 0.05, slide: 130 });
        break;
      case "angry":
        this.tone(330, 0.12, { type: "square", gain: 0.035, slide: 220 });
        this.tone(250, 0.16, { type: "square", gain: 0.035, slide: 170, delay: 0.12 });
        break;
      case "honk":
        this.tone(310, 0.16, { type: "square", gain: 0.05, slide: 280 });
        this.tone(300, 0.22, { type: "square", gain: 0.05, slide: 250, delay: 0.2 });
        break;
      case "bark":
        this.tone(240, 0.09, { type: "sawtooth", gain: 0.07, slide: 150 });
        this.tone(260, 0.11, { type: "sawtooth", gain: 0.07, slide: 150, delay: 0.16 });
        break;
      case "chirp":
        [2100, 2600, 2300, 2800].forEach((f, i) => this.tone(f, 0.07, { gain: 0.04, delay: i * 0.08 }));
        break;
      case "squawk":
        this.tone(700, 0.18, { type: "sawtooth", gain: 0.04, slide: 1200 });
        break;
      case "thunder":
        this.noise(1.2, { gain: 0.22, cutoff: 260 });
        break;
      case "munch":
        this.noise(0.07, { gain: 0.07, cutoff: 1800 });
        this.noise(0.07, { gain: 0.07, cutoff: 1800, delay: 0.13 });
        break;
      case "splash":
        this.noise(0.35, { gain: 0.1, cutoff: 900 });
        break;
      case "sweep":
        this.noise(0.25, { gain: 0.05, cutoff: 3000 });
        break;
      case "win":
        [523, 659, 784, 1047].forEach((f, i) => this.tone(f, 0.22, { type: "triangle", delay: i * 0.13 }));
        break;
      case "lose":
        [392, 330, 262].forEach((f, i) => this.tone(f, 0.3, { type: "triangle", delay: i * 0.2 }));
        break;
      default:
        this.tone(660, 0.05, { gain: 0.04 });
    }
  }
}
