// Builds the pitch deck from docs/pitch/deck.html: one PNG per slide, a PDF, and slides.json for build_pptx.py.
// Needs Google Chrome and puppeteer-core (npm i puppeteer-core). Usage, from docs/pitch/:
//   node build_deck.mjs --tests 352 --poster demo-poster.png
import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const arg = (name, fallback) => { const i = process.argv.indexOf(`--${name}`); return i > 0 ? process.argv[i + 1] : fallback; };
const tests = arg('tests', '');
const poster = arg('poster', 'demo-poster.png');
const chrome = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

const browser = await puppeteer.launch({ executablePath: chrome, headless: true });
const page = await browser.newPage();
await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
await page.goto('file://' + path.join(here, 'deck.html'), { waitUntil: 'load' });
await page.evaluate((count, posterSrc) => {
  document.body.innerHTML = document.body.innerHTML.replaceAll('__TESTS__', count);
  for (const frame of document.querySelectorAll('[data-video]')) {
    frame.textContent = '';
    const img = document.createElement('img');
    img.src = posterSrc;
    img.style.cssText = 'width:100%;height:100%;object-fit:contain;border-radius:24px';
    frame.appendChild(img);
  }
}, tests, poster);
await page.evaluate(() => Promise.all([...document.images].map((img) => img.complete ? null : new Promise((r) => { img.onload = img.onerror = r; }))));

fs.mkdirSync(path.join(here, 'slides'), { recursive: true });
const slides = await page.$$('section.slide');
const meta = [];
for (const [i, slide] of slides.entries()) {
  const file = `slides/slide-${String(i + 1).padStart(2, '0')}.png`;
  await slide.screenshot({ path: path.join(here, file) });
  const info = await slide.evaluate((el) => {
    const frame = el.querySelector('[data-video]');
    const box = frame ? (() => { const r = frame.getBoundingClientRect(), s = el.getBoundingClientRect(); return { x: r.x - s.x, y: r.y - s.y, w: r.width, h: r.height }; })() : null;
    return { notes: el.dataset.notes || '', video: box };
  });
  meta.push({ image: file, ...info });
}
fs.writeFileSync(path.join(here, 'slides', 'slides.json'), JSON.stringify(meta, null, 2));
await page.pdf({ path: path.join(here, 'Club-des-Affaires-pitch.pdf'), width: '1920px', height: '1080px', printBackground: true });
await browser.close();
console.log(`${meta.length} slides, PDF written`);
