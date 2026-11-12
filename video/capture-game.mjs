// Captures crisp footage of the running game for the film.
//   python -m zoo play --no-browser --port 8765      (in another terminal)
//   node capture-game.mjs http://127.0.0.1:8765 before 14
// Writes assets/game/<name>/f_000.jpg ... plus index.json (timestamps in seconds).
import fs from "node:fs";
import puppeteer from "puppeteer-core";

const CHROME = process.env.CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const [url = "http://127.0.0.1:8765", name = "before", seconds = "14"] = process.argv.slice(2);
const dir = `assets/game/${name}`;
fs.rmSync(dir, { recursive: true, force: true });
fs.mkdirSync(dir, { recursive: true });

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: true,
  args: ["--mute-audio"],
  defaultViewport: { width: 1900, height: 1000, deviceScaleFactor: 1 },
});
const page = await browser.newPage();
await page.goto(url, { waitUntil: "networkidle0" });
await page.evaluate(() => document.fonts.ready);
await new Promise((r) => setTimeout(r, 800));

const stage = await page.$("#world");
const box = await stage.boundingBox();
await page.screenshot({ path: `${dir}/title.jpg`, type: "jpeg", quality: 90, clip: box });
await page.evaluate(() => {
  const b = [...document.querySelectorAll("button")].find((x) => /open the gates/i.test(x.innerText));
  b?.click();
});

// Screencast: Chrome pushes a JPEG every time the page repaints (20 to 30 per second here).
const frames = [];
const client = await page.createCDPSession();
let t0 = null;
client.on("Page.screencastFrame", ({ data, metadata, sessionId }) => {
  if (t0 === null) t0 = metadata.timestamp;
  const file = `f_${String(frames.length).padStart(4, "0")}.jpg`;
  fs.writeFileSync(`${dir}/${file}`, Buffer.from(data, "base64"));
  frames.push({ t: Number((metadata.timestamp - t0).toFixed(3)), file });
  client.send("Page.screencastFrameAck", { sessionId }).catch(() => {});
});
await client.send("Page.startScreencast", { format: "jpeg", quality: 90, everyNthFrame: 1 });

// Play a little so the scene is alive: click along the visitor queue, then the pens.
const spots = [[0.25, 0.82], [0.3, 0.82], [0.78, 0.3], [0.35, 0.82], [0.4, 0.82], [0.9, 0.72], [0.27, 0.82], [0.78, 0.72]];
const start = Date.now();
let n = 0;
while ((Date.now() - start) / 1000 < Number(seconds)) {
  const [fx, fy] = spots[n % spots.length];
  await page.mouse.click(box.x + box.width * fx, box.y + box.height * fy);
  n += 1;
  await new Promise((r) => setTimeout(r, 1300));
}
await client.send("Page.stopScreencast");
fs.writeFileSync(`${dir}/index.json`, JSON.stringify({ page: [1900, 1000], box, frames }));
console.log(name, frames.length, "frames", JSON.stringify(box));
await browser.close();
