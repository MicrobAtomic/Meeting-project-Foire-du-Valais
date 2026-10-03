// Records the demo scenario as raw frames (CDP screencast at device resolution) + scene markers.
// Usage: BASE=http://127.0.0.1:8010 node record_demo.mjs OUT_DIR
// Produces OUT_DIR/phone/*.jpg + phone.ffconcat, OUT_DIR/desk/*.jpg + desk.ffconcat, OUT_DIR/markers.json
import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
import path from 'node:path';

const base = process.env.BASE || 'http://127.0.0.1:8010';
const out = process.argv[2];
const PASSWORD = 'club-demo-2026';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(out, { recursive: true });

const browser = await puppeteer.launch({
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  headless: true,
  args: ['--hide-scrollbars', '--force-color-profile=srgb'],
});

async function session(email, viewport) {
  const context = await browser.createBrowserContext();
  const page = await context.newPage();
  await page.setViewport(viewport);
  await page.setCookie({ name: 'django_language', value: 'en', url: base });
  await page.goto(base + '/connexion/', { waitUntil: 'networkidle0' });
  await page.type('#id_username', email);
  await page.type('#id_password', PASSWORD);
  await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle0' }), page.click('main form button[type=submit]')]);
  page.on('pageerror', (e) => console.error('pageerror', e.message));
  return page;
}

async function record(page, name, size) {
  const dir = path.join(out, name);
  fs.mkdirSync(dir);
  const client = await page.createCDPSession();
  const frames = [];
  const writes = [];
  client.on('Page.screencastFrame', ({ data, metadata, sessionId }) => {
    const file = path.join(dir, String(frames.length).padStart(5, '0') + '.jpg');
    frames.push({ file, t: metadata.timestamp });
    writes.push(fs.promises.writeFile(file, Buffer.from(data, 'base64')));
    client.send('Page.screencastFrameAck', { sessionId }).catch(() => {});
  });
  await client.send('Page.startScreencast', { format: 'jpeg', quality: 92, maxWidth: size.w, maxHeight: size.h, everyNthFrame: 1 });
  const start = Date.now() / 1000;
  const markers = [];
  return {
    mark(label) { markers.push({ label, t: Date.now() / 1000 - start }); console.log(name, label, (Date.now() / 1000 - start).toFixed(2)); },
    async stop() {
      const end = Date.now() / 1000;
      await client.send('Page.stopScreencast');
      await Promise.all(writes);
      // ffconcat with the real duration of every frame (variable frame rate) -> converted to 30 fps later
      const t0 = start;
      const lines = ['ffconcat version 1.0'];
      // hold the first frame from the start of the recording
      frames.forEach((f, i) => {
        const next = i + 1 < frames.length ? frames[i + 1].t : end;
        const from = i === 0 ? t0 : f.t;
        lines.push(`file '${path.basename(f.file)}'`, `duration ${Math.max(next - from, 0.001).toFixed(4)}`);
      });
      lines.push(`file '${path.basename(frames[frames.length - 1].file)}'`);
      fs.writeFileSync(path.join(dir, 'list.ffconcat'), lines.join('\n') + '\n');
      return { duration: end - start, markers, frames: frames.length };
    },
  };
}

async function tap(page, selector, { text } = {}) {
  let handle;
  if (text) {
    handle = await page.waitForFunction(
      (sel, txt) => [...document.querySelectorAll(sel)].find((el) => el.textContent.includes(txt) && el.offsetParent !== null),
      {}, selector, text,
    );
    handle = handle.asElement();
  } else {
    handle = await page.waitForSelector(selector, { visible: true });
  }
  await handle.evaluate((el) => el.scrollIntoView({ behavior: 'smooth', block: 'center' }));
  await sleep(700);
  const box = await handle.boundingBox();
  await page.evaluate(({ x, y }) => {
    const dot = document.createElement('div');
    Object.assign(dot.style, {
      position: 'fixed', left: `${x - 24}px`, top: `${y - 24}px`, width: '48px', height: '48px', borderRadius: '50%',
      background: 'rgba(185,28,28,.30)', border: '3px solid rgba(185,28,28,.85)', zIndex: 2147483647,
      pointerEvents: 'none', transition: 'transform .45s ease-out, opacity .45s ease-out',
    });
    document.body.appendChild(dot);
    setTimeout(() => { dot.style.transform = 'scale(1.7)'; dot.style.opacity = '0'; }, 60);
    setTimeout(() => dot.remove(), 650);
  }, { x: box.x + box.width / 2, y: box.y + box.height / 2 });
  await sleep(380);
  await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle0' }).catch(() => {}), handle.click()]);
}

async function scrollTo(page, selector, block = 'start') {
  await page.evaluate((sel, b) => {
    const el = document.querySelector(sel);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: b });
  }, selector, block);
}

async function scrollBy(page, y) {
  await page.evaluate((dy) => window.scrollBy({ top: dy, behavior: 'smooth' }), y);
}

// ---------------------------------------------------------------- phone: Camille
const phone = await session('camille.rey@example.com', { width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
await phone.goto(base + '/album/?aide=marche-alemanique', { waitUntil: 'networkidle0' });
const rp = await record(phone, 'phone', { w: 780, h: 1688 });
rp.mark('find');
await sleep(4500);
await phone.evaluate(() => {
  const card = [...document.querySelectorAll('main a[href*="/membres/"]')]
    .find((el) => el.textContent.includes('Lukas Imboden'));
  if (!card) throw new Error('Lukas is missing from the filtered album');
  card.scrollIntoView({ behavior: 'smooth', block: 'center' });
});
await sleep(5500);

rp.mark('intros');
await phone.goto(base + '/evenements/4/', { waitUntil: 'networkidle0' });
await sleep(1500);
await scrollTo(phone, 'section h2.text-lg', 'start');
await sleep(10000);

rp.mark('scan');
await phone.goto(base + '/m/demo-lukas/', { waitUntil: 'networkidle0' });
await sleep(5500);
await tap(phone, 'main form button[type=submit]');
rp.mark('unlocked');
await sleep(4000);
await scrollBy(phone, 520);
await sleep(5000);

rp.mark('bingo');
await phone.goto(base + '/evenements/4/bingo/', { waitUntil: 'networkidle0' });
await sleep(1200);
await scrollTo(phone, 'main ol', 'center');
await sleep(8000);

rp.mark('counts');
await phone.goto(base + '/accueil/', { waitUntil: 'networkidle0' });
await sleep(2000);
await scrollBy(phone, 330);
await sleep(7000);
const phoneResult = await rp.stop();

// ---------------------------------------------------------------- desktop: the team
const desk = await session('equipe@example.com', { width: 1280, height: 800, deviceScaleFactor: 1.5 });
await desk.goto(base + '/staff/', { waitUntil: 'networkidle0' });
const rd = await record(desk, 'desk', { w: 1920, h: 1200 });
rd.mark('staff');
await sleep(3000);
await tap(desk, 'a.btn', { text: 'Prepare' });
await sleep(1500);
await tap(desk, 'button.btn', { text: 'Generate the seating plan' });
await sleep(2000);
await scrollTo(desk, 'section.break-inside-avoid', 'start');
await sleep(7000);
const deskResult = await rd.stop();

fs.writeFileSync(path.join(out, 'markers.json'), JSON.stringify({ phone: phoneResult, desk: deskResult }, null, 2));
console.log(JSON.stringify({ phone: { duration: phoneResult.duration, frames: phoneResult.frames }, desk: { duration: deskResult.duration, frames: deskResult.frames } }));
await browser.close();
