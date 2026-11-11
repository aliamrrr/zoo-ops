/**
 * The park itself: where everything stands, and the static painting of ground, paths, pond,
 * pens, buildings and plants. Painted once into an offscreen canvas, in a 1280 x 720 space.
 */
import { OUTLINE, acorn, bowl, coin, heart, line, oval, poly, rrect, text } from "./art.js";

export const W = 1280;
export const H = 720;

const WOOD = "#7d5a3c";
const SAND = "#f8e6b8";
const SAND_EDGE = "#e3c98f";
const SHADOW = "rgba(40,80,60,0.2)";

export const P = {
  spawn: { x: 150, y: 760 },
  entry: { x: 152, y: 492 },
  gate: { x: 150, y: 640 },
  goose: { x: 222, y: 630 },
  queue: [520, 468, 416, 364, 312, 260].map((x) => ({ x, y: 486 })),
  serve: { x: 640, y: 446 },
  plaza: { x: 640, y: 470 },
  exit: { x: 640, y: 780 },
  owl: { x: 640, y: 262 },
  bridgeTop: { x: 640, y: 312 },
  bridgeFoot: { x: 640, y: 408 },
  cache: { x: 468, y: 410 },
  shelf: { x: 412, y: 398 },
  squirrel: { x: 530, y: 418 },
  fox: { x: 704, y: 430 },
  perch: { x: 812, y: 346 },
  perchFoot: { x: 776, y: 420 },
  lookout: { x: 105, y: 330 },
  meerkat: { x: 105, y: 199 },
  burrows: { x: 250, y: 378 },
  mole: { x: 250, y: 380 },
  nestTree: { x: 372, y: 300 },
  nest: { x: 398, y: 184 },
  adoption: { x: 395, y: 642 },
  beaver: { x: 456, y: 654 },
  families: [{ x: 312, y: 668 }, { x: 348, y: 672 }],
  anthill: { x: 548, y: 654 },
  chest: { x: 716, y: 614 },
  kennel: { x: 812, y: 652 },
  dog: { x: 766, y: 666 },
  kitchen: { x: 1080, y: 364 },
  staffDoor: { x: 880, y: 770 },
};

export const PENS = {
  lion: { x: 905, y: 132, w: 165, h: 178, ground: "savanna" },
  otter: { x: 1090, y: 132, w: 165, h: 178, ground: "pond" },
  penguin: { x: 905, y: 434, w: 165, h: 178, ground: "ice" },
  miso: { x: 1090, y: 434, w: 165, h: 178, ground: "garden" },
};

export const LAMPS = [[214, 520], [542, 540], [742, 540], [868, 338], [1000, 404], [1182, 404],
  [584, 404], [696, 400]];

/** Where each pattern's sign hangs in the world. */
export const SIGNS = {
  "01": { x: 468, y: 304, dx: -40 },
  "02": { x: 150, y: 520 },
  "03": { x: 812, y: 280, dx: -30 },
  "04": { x: 1080, y: 250 },
  "05": { x: 105, y: 352, below: true },
  "06": { x: 250, y: 314 },
  "07": { x: 395, y: 532 },
  "08": { x: 548, y: 596 },
  "09": { x: 812, y: 564 },
  "10": { x: 360, y: 102, below: true },
};

function rng(seed) {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function beam(ctx, x1, y1, x2, y2, width, color, edge = WOOD) {
  line(ctx, [x1, y1, x2, y2], edge, width + 4);
  line(ctx, [x1, y1, x2, y2], color, width);
}

function dome(ctx, x, y, rx, ry, fill, stroke, lw = 2.5) {
  ctx.beginPath();
  ctx.ellipse(x, y, rx, ry, 0, Math.PI, Math.PI * 2);
  ctx.closePath();
  ctx.fillStyle = fill;
  ctx.fill();
  ctx.strokeStyle = stroke;
  ctx.lineWidth = lw;
  ctx.lineJoin = "round";
  ctx.stroke();
}

function flower(ctx, x, y, color, size = 1) {
  for (let i = 0; i < 5; i += 1) {
    const angle = (i / 5) * Math.PI * 2;
    oval(ctx, x + Math.cos(angle) * 3 * size, y + Math.sin(angle) * 3 * size, 2.3 * size,
      2.3 * size, color);
  }
  oval(ctx, x, y, 1.9 * size, 1.9 * size, "#ffd23f");
}

const TREE_TONES = [["#3f9d63", "#58b56d", "#8bd684"], ["#3a9a70", "#4fb382", "#86d6a6"],
  ["#5a9f4a", "#74b95a", "#a5d97c"]];

function tree(ctx, x, y, s = 1, tone = 0) {
  const [dark, mid, light] = TREE_TONES[tone % 3];
  oval(ctx, x, y + 2, 34 * s, 10 * s, SHADOW);
  rrect(ctx, x - 7 * s, y - 34 * s, 14 * s, 36 * s, 5 * s, "#a9744a", WOOD, 2);
  const blobs = [[0, -78, 32], [-24, -58, 25], [24, -58, 25], [0, -50, 27]];
  for (const [dx, dy, r] of blobs) oval(ctx, x + dx * s, y + dy * s, r * s + 2.5, r * s + 2.5, dark);
  for (const [dx, dy, r] of blobs) oval(ctx, x + dx * s, y + dy * s, r * s, r * s, mid);
  oval(ctx, x - 10 * s, y - 88 * s, 14 * s, 9 * s, light, null, 0, -0.3);
  oval(ctx, x + 18 * s, y - 64 * s, 7 * s, 5 * s, light);
  oval(ctx, x - 22 * s, y - 56 * s, 6 * s, 4 * s, light);
}

function bush(ctx, x, y, s = 1, tone = 0, bloom = null) {
  const [dark, mid, light] = TREE_TONES[tone % 3];
  oval(ctx, x, y + 2, 24 * s, 6 * s, SHADOW);
  const blobs = [[-12, -8, 12], [10, -9, 13], [0, -15, 13]];
  for (const [dx, dy, r] of blobs) oval(ctx, x + dx * s, y + dy * s, r * s + 2, r * s + 2, dark);
  for (const [dx, dy, r] of blobs) oval(ctx, x + dx * s, y + dy * s, r * s, r * s, mid);
  oval(ctx, x - 4 * s, y - 20 * s, 6 * s, 4 * s, light);
  if (bloom) {
    flower(ctx, x - 10 * s, y - 12 * s, bloom, s);
    flower(ctx, x + 9 * s, y - 15 * s, bloom, s);
    flower(ctx, x + 1 * s, y - 5 * s, bloom, s);
  }
}

function ground(ctx, rand) {
  const grass = ctx.createRadialGradient(640, 360, 120, 640, 360, 820);
  grass.addColorStop(0, "#b9eb95");
  grass.addColorStop(1, "#8dd67c");
  ctx.fillStyle = grass;
  ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 36; i += 1) {
    oval(ctx, rand() * W, rand() * H, 50 + rand() * 110, 24 + rand() * 46,
      i % 2 ? "rgba(255,255,255,0.08)" : "rgba(52,140,80,0.07)");
  }
  for (let i = 0; i < 320; i += 1) {
    const x = rand() * W;
    const y = rand() * H;
    line(ctx, [x - 3, y - 6, x, y, x + 3, y - 6], "rgba(86,170,96,0.75)", 1.6);
  }
  const blooms = ["#ffffff", "#ffd1e0", "#fff0a0", "#d9c8ff"];
  for (let i = 0; i < 110; i += 1) flower(ctx, rand() * W, 100 + rand() * (H - 100), blooms[i % 4]);
}

const ROADS = [
  { w: 46, pts: [[150, 780], [150, 560], [152, 500], [205, 486], [330, 486], [540, 486]] },
  { w: 42, pts: [[745, 478], [830, 455], [870, 395], [930, 372], [1300, 372]] },
  { w: 46, pts: [[640, 505], [640, 780]] },
  { w: 20, pts: [[150, 505], [125, 420], [108, 350]] },
  { w: 20, pts: [[205, 486], [236, 440], [248, 400]] },
  { w: 20, pts: [[332, 484], [354, 400], [368, 322]] },
  { w: 20, pts: [[585, 512], [500, 572], [428, 632]] },
  { w: 20, pts: [[615, 525], [578, 590], [554, 636]] },
  { w: 20, pts: [[690, 520], [742, 580], [792, 636]] },
];

function trace(ctx, pts) {
  ctx.beginPath();
  ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length - 1; i += 1) {
    const mx = (pts[i][0] + pts[i + 1][0]) / 2;
    const my = (pts[i][1] + pts[i + 1][1]) / 2;
    ctx.quadraticCurveTo(pts[i][0], pts[i][1], mx, my);
  }
  ctx.lineTo(pts[pts.length - 1][0], pts[pts.length - 1][1]);
}

function roads(ctx, rand) {
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  for (const [color, extra] of [[SAND_EDGE, 8], [SAND, 0]]) {
    for (const road of ROADS) {
      trace(ctx, road.pts);
      ctx.strokeStyle = color;
      ctx.lineWidth = road.w + extra;
      ctx.stroke();
    }
    oval(ctx, P.plaza.x, P.plaza.y, 144 + extra / 2, 62 + extra / 2, color);
  }
  ctx.setLineDash([3, 13]);
  ctx.strokeStyle = "rgba(214,180,120,0.9)";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.ellipse(P.plaza.x, P.plaza.y, 112, 44, 0, 0, Math.PI * 2);
  ctx.stroke();
  ctx.setLineDash([]);
  for (const road of ROADS) {
    for (let i = 0; i < road.pts.length - 1; i += 1) {
      const [ax, ay] = road.pts[i];
      const [bx, by] = road.pts[i + 1];
      const count = Math.ceil(Math.hypot(bx - ax, by - ay) / 16);
      for (let n = 0; n < count; n += 1) {
        const k = rand();
        const spread = (rand() - 0.5) * (road.w - 12);
        oval(ctx, ax + (bx - ax) * k + spread * 0.7, ay + (by - ay) * k + spread * 0.7,
          1.6 + rand() * 1.6, 1.2 + rand(), "rgba(214,180,120,0.8)");
      }
    }
  }
}

function pond(ctx) {
  oval(ctx, 640, 270, 214, 126, SAND, SAND_EDGE, 3);
  const water = ctx.createLinearGradient(0, 150, 0, 390);
  water.addColorStop(0, "#97e0f6");
  water.addColorStop(1, "#57bfe9");
  oval(ctx, 640, 270, 200, 112, water, "#3fa3d1", 3);
  oval(ctx, 640, 286, 166, 84, "rgba(48,140,210,0.2)");
  ctx.setLineDash([22, 30]);
  ctx.strokeStyle = "rgba(255,255,255,0.6)";
  ctx.lineWidth = 3;
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.ellipse(640, 270, 190, 103, 0, 0, Math.PI * 2);
  ctx.stroke();
  ctx.setLineDash([]);

  for (const [x, y, bloom] of [[520, 306, true], [772, 246, false], [556, 212, true],
    [742, 330, false], [716, 196, true], [486, 252, false]]) {
    oval(ctx, x, y, 13, 8, "#6fc46a", "#3f9d63", 2);
    line(ctx, [x, y, x + 9, y - 5], "#3f9d63", 2);
    if (bloom) flower(ctx, x - 2, y - 2, "#ffb3cd", 1.1);
  }
  for (const [x, y] of [[452, 300], [460, 312], [826, 292], [818, 306]]) {
    line(ctx, [x, y, x + 2, y - 26], "#5a9f4a", 3);
    oval(ctx, x + 2, y - 30, 3.5, 8, "#9b6a42", WOOD, 1.5);
  }

  oval(ctx, 640, 260, 90, 53, SAND, SAND_EDGE, 3);
  oval(ctx, 640, 256, 80, 45, "#aee58f", "#7cc96f", 2.5);
  flower(ctx, 590, 262, "#ffffff");
  flower(ctx, 694, 276, "#ffd1e0");

  const top = 300;
  const foot = 410;
  rrect(ctx, 614, top, 52, foot - top, 6, "#c98e5a", WOOD, 3);
  for (let y = top + 10; y < foot - 4; y += 11) line(ctx, [617, y, 663, y], "#a9744a", 2);
  for (const x of [614, 666]) {
    beam(ctx, x, top + 2, x, foot - 2, 4, "#e2b98a");
    for (const y of [top + 4, (top + foot) / 2, foot - 4]) oval(ctx, x, y, 5, 5, "#e2b98a", WOOD, 2);
  }

  beam(ctx, 572, 300, 572, 262, 5, "#c98e5a");
  rrect(ctx, 534, 232, 78, 32, 9, "#fff7e0", "#a9744a", 3);
  text(ctx, "ASK ME!", 573, 249, { size: 15, color: "#a9623a", weight: 800 });

  beam(ctx, 708, 292, 708, 214, 5, "#e8e8f0", "#8a8fa0");
  ctx.save();
  ctx.beginPath();
  ctx.ellipse(708, 216, 46, 30, 0, Math.PI, Math.PI * 2);
  ctx.closePath();
  ctx.clip();
  for (let i = 0; i < 6; i += 1) {
    ctx.fillStyle = i % 2 ? "#ffffff" : "#ff8fab";
    ctx.fillRect(662 + i * 15.4, 180, 15.4, 40);
  }
  ctx.restore();
  dome(ctx, 708, 216, 46, 30, "rgba(0,0,0,0)", OUTLINE, 2.5);
  oval(ctx, 708, 186, 4, 4, "#ff8fab", OUTLINE, 2);

  rrect(ctx, 604, 258, 72, 26, 10, "#a9744a", WOOD, 3);
  oval(ctx, 640, 259, 36, 12, "#e2b98a", WOOD, 3);
  oval(ctx, 640, 259, 22, 7, "rgba(0,0,0,0)", "#c98e5a", 2);
  oval(ctx, 640, 259, 9, 3, "rgba(0,0,0,0)", "#c98e5a", 2);
}

function penDecor(ctx, pen, rand) {
  const { x, y, w, h } = pen;
  const cx = x + w / 2;
  if (pen.ground === "savanna") {
    for (let i = 0; i < 26; i += 1) {
      const px = x + 12 + rand() * (w - 24);
      const py = y + 16 + rand() * (h - 28);
      line(ctx, [px - 3, py - 7, px, py, px + 3, py - 7], "#d9b25c", 1.8);
    }
    oval(ctx, x + w - 40, y + 48, 24, 13, "#c5cad3", "#8a93a3", 2.5);
    oval(ctx, x + w - 46, y + 43, 10, 5, "#e3e7ee");
    oval(ctx, x + 34, y + 44, 13, 8, "#c5cad3", "#8a93a3", 2.5);
  } else if (pen.ground === "pond") {
    oval(ctx, cx + 14, y + h - 62, 56, 34, SAND, SAND_EDGE, 2.5);
    oval(ctx, cx + 14, y + h - 62, 49, 28, "#7fd3f2", "#3fa3d1", 2.5);
    oval(ctx, cx + 2, y + h - 70, 16, 5, "rgba(255,255,255,0.6)");
    rrect(ctx, x + 18, y + 36, 46, 14, 7, "#a9744a", WOOD, 2.5);
    oval(ctx, x + 64, y + 43, 5, 7, "#e2b98a", WOOD, 2);
  } else if (pen.ground === "ice") {
    rrect(ctx, x + 14, y + h - 58, w - 28, 40, 16, "#7fd3f2", "#3fa3d1", 2.5);
    oval(ctx, cx - 20, y + h - 46, 18, 4, "rgba(255,255,255,0.7)");
    dome(ctx, x + w - 44, y + 62, 30, 28, "#ffffff", "#9ccbe6", 2.5);
    rrect(ctx, x + w - 54, y + 44, 20, 18, [10, 10, 0, 0], "#5d7ea8");
    for (const [dx, dy] of [[26, 40], [52, 76], [30, 96]]) {
      rrect(ctx, x + dx, y + dy, 20, 12, 4, "#ffffff", "#bfe3f5", 2);
    }
  } else {
    for (let i = 0; i < 16; i += 1) {
      flower(ctx, x + 14 + rand() * (w - 28), y + 20 + rand() * (h - 36),
        ["#ffd1e0", "#ffffff", "#fff0a0"][i % 3]);
    }
    rrect(ctx, x + w - 62, y + 34, 44, 34, 8, "#ffe1ea", "#d9538a", 2.5);
    poly(ctx, [x + w - 68, y + 38, x + w - 12, y + 38, x + w - 40, y + 14], "#f08aa8", "#b8567a", 2.5);
    rrect(ctx, x + w - 48, y + 46, 16, 22, [8, 8, 0, 0], "#7a4a5a");
    oval(ctx, x + 36, y + 52, 11, 11, "#8f7ae6", OUTLINE, 2);
    line(ctx, [x + 29, y + 48, x + 43, y + 56], "#c9bcff", 2);
    line(ctx, [x + 30, y + 56, x + 42, y + 47], "#c9bcff", 2);
  }
}

const PEN_COLORS = {
  savanna: ["#f8e09c", "#e2c070"],
  pond: ["#aee58f", "#7cc96f"],
  ice: ["#f1faff", "#bfe3f5"],
  garden: ["#bdebA4", "#86cf78"],
};

function pens(ctx, rand, names) {
  for (const [id, pen] of Object.entries(PENS)) {
    const { x, y, w, h } = pen;
    const [fill, edge] = PEN_COLORS[pen.ground];
    oval(ctx, x + w / 2, y + h + 4, w / 2, 10, SHADOW);
    rrect(ctx, x, y, w, h, 20, fill, edge, 3);
    penDecor(ctx, pen, rand);
    bowl(ctx, x + 28, y + h - 22, 13, false);

    rrect(ctx, x + 2, y + 2, w - 4, h - 4, 18, "rgba(0,0,0,0)", "#b77d4c", 4);
    const posts = [];
    for (let px = x + 12; px <= x + w - 10; px += 23.5) posts.push([px, y + 2], [px, y + h - 2]);
    for (let py = y + 26; py <= y + h - 20; py += 24) posts.push([x + 2, py], [x + w - 2, py]);
    for (const [px, py] of posts) rrect(ctx, px - 3.5, py - 13, 7, 17, 3.5, "#e2b98a", WOOD, 2);

    rrect(ctx, x + w / 2 - 40, y - 20, 80, 26, 9, "#fff7e0", "#a9744a", 3);
    text(ctx, names[id] || id, x + w / 2, y - 6, { size: 16, color: "#8a5a34", weight: 800 });
  }
}

function buildings(ctx) {
  // Lookout tower (observability)
  const tower = P.lookout;
  oval(ctx, tower.x, tower.y + 2, 50, 11, SHADOW);
  for (const side of [-1, 1]) beam(ctx, tower.x + side * 36, tower.y, tower.x + side * 26, 208, 7, "#c98e5a");
  beam(ctx, tower.x - 33, tower.y - 34, tower.x + 28, 232, 4, "#e2b98a");
  beam(ctx, tower.x + 33, tower.y - 34, tower.x - 28, 232, 4, "#e2b98a");
  for (let y = tower.y - 8; y > 214; y -= 16) line(ctx, [tower.x - 8, y, tower.x + 8, y], WOOD, 3);
  line(ctx, [tower.x - 8, tower.y, tower.x - 8, 210], WOOD, 3);
  line(ctx, [tower.x + 8, tower.y, tower.x + 8, 210], WOOD, 3);
  for (const side of [-1, 1]) beam(ctx, tower.x + side * 38, 200, tower.x + side * 38, 142, 4, "#c98e5a");
  rrect(ctx, tower.x - 46, 198, 92, 14, 5, "#d9a066", WOOD, 2.5);
  rrect(ctx, tower.x - 46, 176, 92, 6, 3, "#e2b98a", WOOD, 2);
  poly(ctx, [tower.x - 58, 144, tower.x + 58, 144, tower.x + 30, 106, tower.x - 30, 106], "#ef6f6c",
    "#a8413f", 3);
  line(ctx, [tower.x - 44, 132, tower.x + 44, 132], "#ff9d9a", 3);
  line(ctx, [tower.x, 106, tower.x, 84], OUTLINE, 2.5);
  poly(ctx, [tower.x, 84, tower.x + 20, 90, tower.x, 97], "#2fb8a6", OUTLINE, 2);

  // Burrows (database)
  const burrow = P.burrows;
  for (const [dx, dy, r] of [[-48, 4, 26], [46, 6, 24], [0, 0, 34]]) {
    oval(ctx, burrow.x + dx, burrow.y + dy + 2, r + 4, 7, SHADOW);
    dome(ctx, burrow.x + dx, burrow.y + dy, r, r * 0.8, "#b98a5e", WOOD);
    oval(ctx, burrow.x + dx - r * 0.3, burrow.y + dy - r * 0.5, r * 0.3, r * 0.14, "#d1a67c", null, 0, -0.4);
    oval(ctx, burrow.x + dx, burrow.y + dy - r * 0.18, r * 0.5, r * 0.26, "#5a3d2b");
  }
  rrect(ctx, burrow.x + 62, burrow.y - 34, 30, 22, 4, "#e2b98a", WOOD, 2.5);
  line(ctx, [burrow.x + 66, burrow.y - 23, burrow.x + 88, burrow.y - 23], WOOD, 2);
  oval(ctx, burrow.x + 77, burrow.y - 29, 2, 2, WOOD);
  oval(ctx, burrow.x + 77, burrow.y - 18, 2, 2, WOOD);

  // Nest tree (deploys)
  const nt = P.nestTree;
  oval(ctx, nt.x, nt.y + 2, 44, 12, SHADOW);
  rrect(ctx, nt.x - 13, 168, 26, nt.y - 166, 10, "#a9744a", WOOD, 3);
  beam(ctx, nt.x + 4, 222, P.nest.x + 8, 192, 8, "#a9744a");
  for (const [dx, dy, r] of [[0, -176, 54], [-40, -140, 40], [42, -150, 40], [0, -128, 44]]) {
    oval(ctx, nt.x + dx, nt.y + dy, r + 3, r + 3, "#3f9d63");
  }
  for (const [dx, dy, r] of [[0, -176, 54], [-40, -140, 40], [42, -150, 40], [0, -128, 44]]) {
    oval(ctx, nt.x + dx, nt.y + dy, r, r, "#58b56d");
  }
  oval(ctx, nt.x - 18, nt.y - 198, 22, 13, "#8bd684", null, 0, -0.3);
  oval(ctx, nt.x + 38, nt.y - 166, 10, 7, "#8bd684");
  oval(ctx, P.nest.x, P.nest.y + 3, 27, 12, "#b98a5e", WOOD, 2.5);
  for (const dx of [-16, -6, 6, 16]) line(ctx, [P.nest.x + dx, P.nest.y, P.nest.x + dx + 5, P.nest.y + 9], "#8f6040", 2);

  // Nut store (cache)
  const store = P.cache;
  oval(ctx, store.x, store.y + 2, 54, 12, SHADOW);
  line(ctx, [store.x + 4, 318, store.x + 14, 300], WOOD, 7);
  oval(ctx, store.x, store.y - 38, 46, 42, "#f1c27e", WOOD, 3);
  dome(ctx, store.x, store.y - 56, 55, 42, "#9b6a42", WOOD, 3);
  for (let row = 0; row < 3; row += 1) {
    for (let i = -3 + (row % 2) * 0.5; i <= 3; i += 1) {
      const sx = store.x + i * 14;
      const sy = store.y - 64 - row * 11;
      if (Math.abs(i) * 14 < 50 - row * 12) {
        ctx.beginPath();
        ctx.arc(sx, sy, 6, 0.1 * Math.PI, 0.9 * Math.PI);
        ctx.strokeStyle = "#7a5033";
        ctx.lineWidth = 2;
        ctx.stroke();
      }
    }
  }
  rrect(ctx, store.x - 15, store.y - 36, 30, 38, [15, 15, 3, 3], "#8f6040", WOOD, 2.5);
  oval(ctx, store.x + 8, store.y - 14, 2.5, 2.5, "#ffd23f");
  oval(ctx, store.x + 30, store.y - 44, 8, 8, "#ffe9a8", WOOD, 2.5);
  rrect(ctx, P.shelf.x - 26, P.shelf.y - 4, 52, 20, 5, "#e2b98a", WOOD, 2.5);
  line(ctx, [P.shelf.x - 22, P.shelf.y + 6, P.shelf.x + 22, P.shelf.y + 6], "#c98e5a", 2);

  // Parrot perch (fallback model)
  const perch = P.perch;
  oval(ctx, perch.x, perch.y + 62, 20, 6, SHADOW);
  beam(ctx, perch.x, perch.y + 60, perch.x, perch.y, 6, "#c98e5a");
  beam(ctx, perch.x - 26, perch.y, perch.x + 26, perch.y, 6, "#e2b98a");
  rrect(ctx, perch.x - 26, perch.y + 22, 52, 20, 7, "#fff7e0", "#a9744a", 2.5);
  text(ctx, "backup", perch.x, perch.y + 33, { size: 12, color: "#a9623a", weight: 800 });

  // Adoption office (integrity)
  const home = P.adoption;
  oval(ctx, home.x, home.y + 2, 62, 12, SHADOW);
  rrect(ctx, home.x + 24, home.y - 104, 14, 26, 3, "#e2b98a", WOOD, 2.5);
  rrect(ctx, home.x - 45, home.y - 54, 90, 56, 8, "#fff3d6", WOOD, 3);
  poly(ctx, [home.x - 58, home.y - 48, home.x + 58, home.y - 48, home.x + 36, home.y - 94,
    home.x - 36, home.y - 94], "#f08aa8", "#b8567a", 3);
  line(ctx, [home.x - 46, home.y - 62, home.x + 46, home.y - 62], "#ffb3c8", 3);
  line(ctx, [home.x - 40, home.y - 78, home.x + 40, home.y - 78], "#ffb3c8", 3);
  rrect(ctx, home.x - 12, home.y - 34, 24, 36, [12, 12, 2, 2], "#b9774a", WOOD, 2.5);
  oval(ctx, home.x + 6, home.y - 14, 2.2, 2.2, "#ffd23f");
  rrect(ctx, home.x + 20, home.y - 36, 17, 17, 4, "#bfe9ff", WOOD, 2.5);
  heart(ctx, home.x - 29, home.y - 24, 8, "#ff6b8f");
  heart(ctx, home.x, home.y - 70, 8, "#ffffff");

  // Anthill (async workers)
  const hill = P.anthill;
  oval(ctx, hill.x, hill.y + 2, 50, 10, SHADOW);
  dome(ctx, hill.x, hill.y, 46, 34, "#c99a6a", WOOD, 3);
  dome(ctx, hill.x - 2, hill.y - 20, 30, 24, "#d4a878", WOOD, 2.5);
  dome(ctx, hill.x, hill.y - 36, 15, 14, "#e0b98a", WOOD, 2.5);
  for (const [dx, dy] of [[-22, -8], [18, -10], [-4, -26], [4, -5]]) {
    oval(ctx, hill.x + dx, hill.y + dy, 5.5, 3.6, "#5a3d2b");
  }

  // Treasure chest and kennel (auth)
  const chest = P.chest;
  oval(ctx, chest.x, chest.y + 2, 30, 7, SHADOW);
  rrect(ctx, chest.x - 23, chest.y - 22, 46, 24, 5, "#b9774a", WOOD, 2.5);
  dome(ctx, chest.x, chest.y - 22, 23, 15, "#c98e5a", WOOD, 2.5);
  rrect(ctx, chest.x - 4, chest.y - 37, 8, 39, 0, "#ffc93c", "#b8791a", 1.5);
  rrect(ctx, chest.x - 5, chest.y - 24, 10, 9, 2, "#ffe08a", "#b8791a", 1.5);
  coin(ctx, chest.x + 31, chest.y - 2, 6);
  coin(ctx, chest.x + 38, chest.y - 9, 6);
  coin(ctx, chest.x - 30, chest.y - 3, 6);

  const kennel = P.kennel;
  oval(ctx, kennel.x, kennel.y + 2, 44, 10, SHADOW);
  rrect(ctx, kennel.x - 32, kennel.y - 42, 64, 44, 7, "#ef6f6c", "#a8413f", 3);
  poly(ctx, [kennel.x - 42, kennel.y - 38, kennel.x + 42, kennel.y - 38, kennel.x, kennel.y - 78],
    "#c94f4c", "#8f3533", 3);
  rrect(ctx, kennel.x - 15, kennel.y - 28, 30, 30, [15, 15, 0, 0], "#5a2d2d");
  rrect(ctx, kennel.x - 11, kennel.y - 54, 22, 6, 3, "#ffffff", OUTLINE, 1.5);
  for (const dx of [-11, 11]) {
    oval(ctx, kennel.x + dx, kennel.y - 54, 3.4, 3.4, "#ffffff", OUTLINE, 1.5);
    oval(ctx, kennel.x + dx, kennel.y - 48, 3.4, 3.4, "#ffffff", OUTLINE, 1.5);
  }

  // Kitchen cart (idempotent orders)
  const k = P.kitchen;
  oval(ctx, k.x, k.y + 3, 46, 9, SHADOW);
  for (const dx of [-24, 24]) {
    oval(ctx, k.x + dx, k.y - 4, 8, 8, "#6b5a7a", OUTLINE, 2.5);
    oval(ctx, k.x + dx, k.y - 4, 3, 3, "#d5d0e0");
  }
  rrect(ctx, k.x - 36, k.y - 38, 72, 30, 9, "#5cc8b8", "#2f8f82", 3);
  heart(ctx, k.x, k.y - 22, 6.5, "#ffffff");
  for (const dx of [-32, 32]) beam(ctx, k.x + dx, k.y - 40, k.x + dx, k.y - 72, 4, "#fff3d6");
  rrect(ctx, k.x - 40, k.y - 46, 80, 10, 5, "#fff3d6", WOOD, 2.5);
  bowl(ctx, k.x - 16, k.y - 53, 8);
  bowl(ctx, k.x + 14, k.y - 53, 8);
  ctx.save();
  ctx.beginPath();
  ctx.roundRect(k.x - 46, k.y - 90, 92, 20, 9);
  ctx.clip();
  for (let i = 0; i < 7; i += 1) {
    ctx.fillStyle = i % 2 ? "#ffffff" : "#8f7ae6";
    ctx.fillRect(k.x - 46 + i * 13.2, k.y - 90, 13.2, 20);
  }
  ctx.restore();
  rrect(ctx, k.x - 46, k.y - 90, 92, 20, 9, "rgba(0,0,0,0)", OUTLINE, 2.5);

  // Gate pillars (rate limiter)
  const gate = P.gate;
  for (const side of [-1, 1]) {
    const px = gate.x + side * 46;
    oval(ctx, px, gate.y + 3, 18, 6, SHADOW);
    rrect(ctx, px - 12, gate.y - 78, 24, 80, 6, "#dfe4ec", "#8a93a3", 3);
    line(ctx, [px - 7, gate.y - 50, px + 7, gate.y - 50], "#b9c1cf", 2);
    line(ctx, [px - 7, gate.y - 26, px + 7, gate.y - 26], "#b9c1cf", 2);
    rrect(ctx, px - 16, gate.y - 86, 32, 11, 4, "#c5cad3", "#8a93a3", 3);
  }
}

function plants(ctx, rand) {
  for (let x = -10; x < W + 30; x += 44) {
    tree(ctx, x + rand() * 14, 80 + rand() * 16, 0.85 + rand() * 0.3, Math.floor(rand() * 3));
  }
  const trees = [[30, 160, 1], [208, 190, 0.9], [40, 440, 1], [38, 574, 0.95], [34, 716, 1.05],
    [270, 730, 0.8], [930, 726, 0.8], [1010, 730, 0.8], [1090, 726, 0.8], [1170, 730, 0.8],
    [1246, 724, 0.85], [862, 150, 0.85]];
  trees.forEach(([x, y, s], i) => tree(ctx, x, y, s, i % 3));
  const bushes = [[866, 520, 1, null], [84, 528, 1, "#ffffff"], [236, 560, 0.9, null],
    [588, 716, 1, "#fff0a0"], [694, 712, 0.9, null], [884, 300, 0.9, "#ffd1e0"],
    [300, 250, 0.9, null], [182, 300, 0.8, "#fff0a0"], [476, 712, 1, "#ffd1e0"],
    [856, 606, 0.9, "#ffffff"], [1008, 346, 0.8, null], [1160, 346, 0.8, "#ffd1e0"],
    [300, 610, 0.9, "#ffd1e0"], [450, 150, 0.9, null], [846, 236, 0.9, "#ffffff"],
    [392, 712, 0.8, null], [770, 716, 0.9, "#ffd1e0"]];
  bushes.forEach(([x, y, s, bloom], i) => bush(ctx, x, y, s, i % 3, bloom));

  for (const [x, y] of [[296, 538], [742, 596]]) {
    oval(ctx, x, y + 9, 22, 4, SHADOW);
    rrect(ctx, x - 20, y - 2, 40, 8, 4, "#e2b98a", WOOD, 2.5);
    line(ctx, [x - 14, y + 6, x - 14, y + 11], WOOD, 3);
    line(ctx, [x + 14, y + 6, x + 14, y + 11], WOOD, 3);
  }
  for (const [x, y] of LAMPS) {
    oval(ctx, x, y + 1, 7, 2.5, SHADOW);
    line(ctx, [x, y, x, y - 34], OUTLINE, 4);
    rrect(ctx, x - 5, y - 2, 10, 4, 2, OUTLINE);
    oval(ctx, x, y - 39, 6.5, 6.5, "#fff6c9", OUTLINE, 2.5);
  }
  for (const [x, y, r] of [[560, 572, 7], [730, 392, 6], [200, 420, 6], [880, 430, 8]]) {
    oval(ctx, x, y, r * 1.4, r, "#c5cad3", "#8a93a3", 2);
    oval(ctx, x - r * 0.4, y - r * 0.35, r * 0.5, r * 0.25, "#e3e7ee");
  }
}

export function paintScenery(ctx, names) {
  const rand = rng(11);
  ground(ctx, rand);
  roads(ctx, rand);
  pond(ctx);
  pens(ctx, rand, names);
  buildings(ctx);
  plants(ctx, rand);
  const vignette = ctx.createRadialGradient(640, 360, 380, 640, 360, 800);
  vignette.addColorStop(0, "rgba(20,70,60,0)");
  vignette.addColorStop(1, "rgba(20,70,60,0.2)");
  ctx.fillStyle = vignette;
  ctx.fillRect(0, 0, W, H);
}

/** The arch of the gate, drawn after the visitors so they walk under it. */
export function paintGateFront(ctx, time) {
  const gate = P.gate;
  rrect(ctx, gate.x - 70, gate.y - 116, 140, 34, 14, "#c98e5a", WOOD, 3);
  rrect(ctx, gate.x - 62, gate.y - 110, 124, 22, 10, "#e2b98a");
  text(ctx, "ZOO", gate.x, gate.y - 97, { size: 22, color: "#ffffff", stroke: "#8a5a34", weight: 800 });
  const colors = ["#ff8fab", "#ffd23f", "#6cc5f2", "#8f7ae6", "#7fd06c"];
  for (let i = 0; i < 5; i += 1) {
    const k = (i + 0.5) / 5;
    const x = gate.x - 34 + k * 68;
    const y = gate.y - 80 + Math.sin(k * Math.PI) * 7 + Math.sin(time * 2 + i) * 0.8;
    poly(ctx, [x - 6, y, x + 6, y, x, y + 11], colors[i], OUTLINE, 1.5);
  }
}

/** Caution tape and a cone in front of a system that is not built yet. */
export function paintConstruction(ctx, x, y, width) {
  ctx.save();
  ctx.beginPath();
  ctx.roundRect(x - width / 2, y - 9, width, 12, 3);
  ctx.clip();
  ctx.fillStyle = "#ffd23f";
  ctx.fillRect(x - width / 2, y - 9, width, 12);
  ctx.strokeStyle = "#4b3757";
  ctx.lineWidth = 5;
  for (let i = -2; i < width / 12 + 2; i += 1) {
    ctx.beginPath();
    ctx.moveTo(x - width / 2 + i * 12, y + 5);
    ctx.lineTo(x - width / 2 + i * 12 + 12, y - 11);
    ctx.stroke();
  }
  ctx.restore();
  rrect(ctx, x - width / 2, y - 9, width, 12, 3, "rgba(0,0,0,0)", OUTLINE, 2);
  for (const side of [-1, 1]) {
    line(ctx, [x + side * (width / 2), y - 12, x + side * (width / 2), y + 12], OUTLINE, 4);
  }
}

export function paintAcorns(ctx, count) {
  for (let i = 0; i < Math.min(count, 8); i += 1) {
    acorn(ctx, P.shelf.x - 18 + (i % 4) * 12, P.shelf.y - 8 - Math.floor(i / 4) * 11, 7);
  }
}
