// Renders the transparent overlays of the demo video (1920x1080): phone bezel, browser window, captions.
// Usage: node video_assets.mjs OUT_DIR captions.json
import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
import path from 'node:path';

const out = process.argv[2];
const captions = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
fs.mkdirSync(out, { recursive: true });

const FONT = `-apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Helvetica, Arial, sans-serif`;
const page0 = (body) => `<!doctype html><html><head><meta charset="utf-8"><style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body { width: 1920px; height: 1080px; background: transparent; font-family: ${FONT}; -webkit-font-smoothing: antialiased; }
  .abs { position: absolute; }
</style></head><body>${body}</body></html>`;

const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true });
const page = await browser.newPage();
await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });

async function render(name, body) {
  await page.setContent(page0(body), { waitUntil: 'load' });
  await page.screenshot({ path: path.join(out, name), omitBackground: true });
}

// Phone: screen 434 x 940 at (350, 60); bezel 20 px, outer radius 64
await render('bezel.png', `
  <div class="abs" style="left:330px;top:40px;width:474px;height:1000px;border:20px solid #292524;border-radius:64px;
       box-shadow:0 0 0 2px #44403c, 0 40px 90px rgba(0,0,0,.55)"></div>`);

// Browser window: content 1440 x 900 at (240, 150), title bar 40 px above
await render('window.png', `
  <div class="abs" style="left:236px;top:106px;width:1448px;height:948px;border:4px solid #44403c;border-radius:18px;
       box-shadow:0 40px 90px rgba(0,0,0,.55)"></div>
  <div class="abs" style="left:240px;top:110px;width:1440px;height:40px;background:#292524;border-radius:14px 14px 0 0;
       display:flex;align-items:center;gap:10px;padding-left:18px">
    <span style="width:14px;height:14px;border-radius:50%;background:#ef4444;display:inline-block"></span>
    <span style="width:14px;height:14px;border-radius:50%;background:#f59e0b;display:inline-block"></span>
    <span style="width:14px;height:14px;border-radius:50%;background:#22c55e;display:inline-block"></span>
    <span style="margin-left:24px;color:#a8a29e;font-size:18px">club-des-affaires · staff</span>
  </div>`);

for (const [i, cap] of captions.phone.entries()) {
  await render(`cap_phone_${i}.png`, `
    <div class="abs" style="left:930px;top:0;width:880px;height:1080px;display:flex;flex-direction:column;justify-content:center">
      <p style="font-size:24px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:#fca5a5">${cap.kicker}</p>
      <p style="margin-top:22px;font-size:66px;line-height:1.08;font-weight:800;color:#fafaf9;letter-spacing:-.01em">${cap.title}</p>
      <p style="margin-top:26px;font-size:36px;line-height:1.35;color:#d6d3d1">${cap.text}</p>
    </div>`);
}
for (const [i, cap] of captions.desk.entries()) {
  await render(`cap_desk_${i}.png`, `
    <div class="abs" style="left:0;top:22px;width:1920px;text-align:center">
      <p style="font-size:44px;font-weight:800;color:#fafaf9">${cap.title} <span style="font-weight:500;color:#d6d3d1">· ${cap.text}</span></p>
    </div>`);
}
await browser.close();
console.log('assets ok');
