// Overlays of the long video (1920x1080, transparent): phone bezel, browser window, one caption per scene
// (title + the narration as subtitle, for viewers without sound). Usage: node long_assets.mjs OUT_DIR
import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const out = process.argv[2];
const scenes = JSON.parse(fs.readFileSync(path.join(here, 'long_scenes.json'), 'utf8'));
fs.mkdirSync(out, { recursive: true });
const FONT = `-apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Helvetica, Arial, sans-serif`;
const wrap = (body) => `<!doctype html><html><head><meta charset="utf-8"><style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body { width: 1920px; height: 1080px; background: transparent; font-family: ${FONT}; -webkit-font-smoothing: antialiased; }
  .abs { position: absolute; }
</style></head><body>${body}</body></html>`;
const browser = await puppeteer.launch({ executablePath: process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true });
const page = await browser.newPage();
await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
async function render(name, body) {
  await page.setContent(wrap(body), { waitUntil: 'load' });
  await page.screenshot({ path: path.join(out, name), omitBackground: true });
}
// phone: screen 434 x 940 at (350, 60)
await render('bezel.png', `<div class="abs" style="left:330px;top:40px;width:474px;height:1000px;border:20px solid #292524;border-radius:64px;box-shadow:0 0 0 2px #44403c, 0 40px 90px rgba(0,0,0,.55)"></div>`);
// desktop: content 1280 x 800 at (320, 120), title bar above, subtitles below
await render('window.png', `
  <div class="abs" style="left:316px;top:76px;width:1288px;height:848px;border:4px solid #44403c;border-radius:18px;box-shadow:0 40px 90px rgba(0,0,0,.55)"></div>
  <div class="abs" style="left:320px;top:80px;width:1280px;height:40px;background:#292524;border-radius:14px 14px 0 0;display:flex;align-items:center;gap:10px;padding-left:18px">
    <span style="width:14px;height:14px;border-radius:50%;background:#ef4444;display:inline-block"></span>
    <span style="width:14px;height:14px;border-radius:50%;background:#f59e0b;display:inline-block"></span>
    <span style="width:14px;height:14px;border-radius:50%;background:#22c55e;display:inline-block"></span>
    <span style="margin-left:24px;color:#a8a29e;font-size:18px">club-des-affaires · events team</span>
  </div>`);
for (const segment of scenes.segments) {
  for (const s of segment.scenes) {
    if (segment.layout === 'phone') {
      await render(`cap_${s.id}.png`, `
        <div class="abs" style="left:930px;top:0;width:900px;height:1080px;display:flex;flex-direction:column;justify-content:center">
          <p style="font-size:24px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:#fca5a5">${s.kicker}</p>
          <p style="margin-top:20px;font-size:60px;line-height:1.08;font-weight:800;color:#fafaf9">${s.title}</p>
          <p style="margin-top:28px;font-size:31px;line-height:1.42;color:#d6d3d1">${s.say}</p>
        </div>`);
    } else {
      await render(`cap_${s.id}.png`, `
        <p class="abs" style="left:0;top:18px;width:1920px;text-align:center;font-size:38px;font-weight:800;color:#fafaf9">
          <span style="color:#fca5a5;font-size:24px;letter-spacing:.14em;text-transform:uppercase;font-weight:700">${s.kicker}</span>&nbsp;&nbsp;${s.title}</p>
        <p class="abs" style="left:160px;top:944px;width:1600px;text-align:center;font-size:29px;line-height:1.38;color:#e7e5e4">${s.say}</p>`);
    }
  }
}
await browser.close();
console.log('assets ok');
