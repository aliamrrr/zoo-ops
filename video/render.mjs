// Renders the film frame by frame with headless Chrome and pipes the frames into ffmpeg.
//   node render.mjs                     full film -> out/zoo-ops.mp4
//   node render.mjs --from 17 --to 31   a section only -> out/zoo-ops-17-31.mp4
//   node render.mjs --still 12.5        one frame -> out/still-12.50.png
//   node render.mjs --sheet 0,5,10      a contact sheet of the given times -> out/sheet.jpg
//   node render.mjs --film film2        the reference-style film (src/film2.html) -> out/zoo-ops-film2.mp4
//   node render.mjs --serve            just serve the preview at http://127.0.0.1:8899/video/src/index.html?play
import { spawn } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, ".."); // repo root, so the film can import the game's art module
const CHROME = process.env.CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 8899;
const args = process.argv.slice(2);
const arg = (name, fallback) => (args.includes(name) ? args[args.indexOf(name) + 1] : fallback);

const TYPES = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".svg": "image/svg+xml", ".jpg": "image/jpeg", ".png": "image/png", ".woff2": "font/woff2" };
const server = http.createServer((req, res) => {
  const file = path.join(ROOT, decodeURIComponent(new URL(req.url, "http://x").pathname));
  if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    res.writeHead(404).end();
    return;
  }
  res.writeHead(200, { "content-type": TYPES[path.extname(file)] || "application/octet-stream", "cache-control": "no-store" });
  fs.createReadStream(file).pipe(res);
});
await new Promise((resolve) => server.listen(PORT, "127.0.0.1", resolve));
const FILM = arg("--film", "film"); // "film" (Zoo Ops identity) or "film2" (reference style)
const url = `http://127.0.0.1:${PORT}/video/src/${FILM === "film" ? "index" : FILM}.html`;

if (args.includes("--serve")) {
  console.log(`Preview: ${url}?play   (space = pause, arrows = scrub, shift+arrows = 1 s)`);
} else {
  fs.mkdirSync(path.join(HERE, "out"), { recursive: true });
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true,
    args: ["--force-color-profile=srgb", "--hide-scrollbars"],
    defaultViewport: { width: 1920, height: 1080, deviceScaleFactor: 1 } });
  const page = await browser.newPage();
  page.on("pageerror", (e) => console.error("PAGE ERROR", e.message));
  page.on("console", (m) => m.type() === "error" && console.error("CONSOLE", m.text()));
  await page.goto(url, { waitUntil: "networkidle0" });
  await page.waitForFunction("window.READY === true", { timeout: 30000 });
  const { duration, fps } = await page.evaluate("window.FILM");
  const frame = async (t, type = "png") => {
    await page.evaluate((time) => window.seek(time), t);
    return page.screenshot({ type, ...(type === "jpeg" ? { quality: 96 } : {}) });
  };

  if (args.includes("--still")) {
    const t = Number(arg("--still"));
    const out = path.join(HERE, "out", `still-${t.toFixed(2)}.png`);
    fs.writeFileSync(out, await frame(t));
    console.log(out);
  } else if (args.includes("--sheet")) {
    const times = arg("--sheet").split(",").map(Number);
    const tmp = fs.mkdtempSync(path.join(HERE, "out", "sheet-"));
    for (const [i, t] of times.entries()) fs.writeFileSync(path.join(tmp, `${String(i).padStart(3, "0")}.jpg`), await frame(t, "jpeg"));
    const cols = Math.min(4, times.length);
    const out = path.join(HERE, "out", arg("--name", "sheet") + ".jpg");
    await new Promise((resolve) => spawn("ffmpeg", ["-v", "error", "-y", "-i", path.join(tmp, "%03d.jpg"), "-vf",
      `scale=640:-1,tile=${cols}x${Math.ceil(times.length / cols)}`, "-frames:v", "1", out], { stdio: "inherit" }).on("close", resolve));
    fs.rmSync(tmp, { recursive: true });
    console.log(out);
  } else {
    const from = Number(arg("--from", 0));
    const to = Number(arg("--to", duration));
    const whole = from === 0 && to === duration;
    const base = FILM === "film" ? "zoo-ops" : `zoo-ops-${FILM}`;
    const out = path.join(HERE, "out", whole ? `${base}.mp4` : `${base}-${from}-${to}.mp4`);
    const ffmpeg = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-framerate", String(fps), "-c:v", "mjpeg", "-i", "-",
      "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
    { stdio: ["pipe", "inherit", "inherit"] });
    const total = Math.round((to - from) * fps);
    const started = Date.now();
    for (let i = 0; i < total; i += 1) {
      const buffer = await frame(from + i / fps, "jpeg");
      if (!ffmpeg.stdin.write(buffer)) await new Promise((resolve) => ffmpeg.stdin.once("drain", resolve));
      if (i % 150 === 0) console.log(`frame ${i}/${total}  ${((Date.now() - started) / 1000).toFixed(0)}s`);
    }
    ffmpeg.stdin.end();
    await new Promise((resolve) => ffmpeg.on("close", resolve));
    console.log(out);
  }
  await browser.close();
  server.close();
}
