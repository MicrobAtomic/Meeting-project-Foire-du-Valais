// Records the LONG demo (voice-over timing) as raw frames (CDP screencast at device resolution) + scene markers.
// Usage: BASE=http://127.0.0.1:8010 node record_demo.mjs OUT_DIR
// Produces OUT_DIR/phone/*.jpg + phone.ffconcat, OUT_DIR/desk/*.jpg + desk.ffconcat, OUT_DIR/markers.json
import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
import path from 'node:path';

const base = process.env.BASE || 'http://127.0.0.1:8010';
const out = process.argv[2];
const timing = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const PAD = 1500;
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


// Each scene: mark, run its actions, then wait until its narration (+PAD) is over.
async function scene(rec, id, actions) {
  const start = Date.now();
  rec.mark(id);
  await actions();
  const left = start + timing[id] * 1000 + PAD - Date.now();
  await sleep(Math.max(left, 600));
}
const PHONE = { width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true };
const DESK = { width: 1280, height: 800, deviceScaleFactor: 1.5 };

async function anonymous(viewport) {
  const context = await browser.createBrowserContext();
  const page = await context.newPage();
  await page.setViewport(viewport);
  await page.setCookie({ name: 'django_language', value: 'en', url: base });
  return page;
}

// 1. A prospect requests an invitation (phone, logged out)
const prospect = await anonymous(PHONE);
await prospect.goto(base + '/', { waitUntil: 'networkidle0' });
const r1 = await record(prospect, 'prospect', { w: 780, h: 1688 });
await scene(r1, 'intro', async () => {});
await scene(r1, 'landing', async () => { await scrollBy(prospect, 600); await sleep(2500); await scrollBy(prospect, 600); });
await scene(r1, 'join', async () => {
  await prospect.goto(base + '/rejoindre/', { waitUntil: 'networkidle0' });
  for (const [field, value] of [['#id_first_name', 'Anna'], ['#id_last_name', 'Bregy'], ['#id_email', 'anna.bregy@example.com'],
                                ['#id_company', 'Bregy Hotels SA'], ['#id_job_title', 'Managing director']]) {
    await prospect.type(field, value, { delay: 18 });
  }
});
await scene(r1, 'thanks', async () => { await tap(prospect, 'main form button[type=submit]'); });
const s1 = await r1.stop();

// 2. The team accepts the request (desktop, admin)
const desk = await session('equipe@example.com', DESK);
await desk.goto(base + '/admin/', { waitUntil: 'networkidle0' });
const r2 = await record(desk, 'admin', { w: 1920, h: 1200 });
await scene(r2, 'admin-guide', async () => {});
await scene(r2, 'accept', async () => {
  await desk.goto(base + '/admin/club/invitationrequest/', { waitUntil: 'networkidle0' });
  await sleep(1200);
  await desk.click('#result_list tbody tr input.action-select');
  await desk.select('select[name=action]', 'accept_requests');
  await sleep(600);
  await Promise.all([desk.waitForNavigation({ waitUntil: 'networkidle0' }), desk.click('button[name=index]')]);
});
const s2 = await r2.stop();

// 3. Camille, a new member, before / during / after the dinner (phone)
const phone = await session('camille.rey@example.com', PHONE);
await phone.goto(base + '/accueil/', { waitUntil: 'networkidle0' });
const r3 = await record(phone, 'member', { w: 780, h: 1688 });
await scene(r3, 'home', async () => { await sleep(5000); await scrollBy(phone, 330); });
await scene(r3, 'album', async () => {
  await phone.goto(base + '/album/?aide=marche-alemanique', { waitUntil: 'networkidle0' });
  await sleep(2500);
  await phone.evaluate(() => { const c = document.querySelector('main a[href*="/membres/"]'); if (c) c.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
});
await scene(r3, 'card', async () => {
  await tap(phone, 'main a[href*="/membres/"]', { text: 'Lukas' });
  await sleep(2500);
  await scrollBy(phone, 420);
});
await scene(r3, 'event', async () => { await phone.goto(base + '/evenements/4/', { waitUntil: 'networkidle0' }); await sleep(2500); await scrollBy(phone, 260); });
await scene(r3, 'intros', async () => { await scrollTo(phone, 'section h2.text-lg', 'start'); });
await scene(r3, 'scan', async () => { await phone.goto(base + '/m/demo-lukas/', { waitUntil: 'networkidle0' }); });
await scene(r3, 'unlocked', async () => { await tap(phone, 'main form button[type=submit]'); await sleep(3500); await scrollBy(phone, 520); });
await scene(r3, 'bingo', async () => { await phone.goto(base + '/evenements/4/bingo/', { waitUntil: 'networkidle0' }); await sleep(800); await scrollTo(phone, 'main ol', 'center'); });
await scene(r3, 'after', async () => { await phone.goto(base + '/accueil/', { waitUntil: 'networkidle0' }); await sleep(800); await scrollBy(phone, 330); });
await scene(r3, 'languages', async () => {
  await phone.evaluate(() => window.scrollTo({ top: 0 }));
  await sleep(400);
  await tap(phone, 'header button[name=language][value=de]');
});
const s3 = await r3.stop();

// 4. The team prepares the dinner (desktop)
await desk.goto(base + '/staff/', { waitUntil: 'networkidle0' });
const r4 = await record(desk, 'team', { w: 1920, h: 1200 });
await scene(r4, 'dashboard', async () => { await sleep(4000); await scrollBy(desk, 500); });
await scene(r4, 'prepare', async () => { await desk.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' })); await sleep(500); await tap(desk, 'a.btn', { text: 'Prepare' }); });
await scene(r4, 'seating', async () => { await tap(desk, 'button.btn', { text: 'Generate the seating plan' }); await sleep(1500); await scrollTo(desk, 'section.break-inside-avoid', 'start'); });
await scene(r4, 'badges', async () => { await desk.goto(base + '/staff/evenements/4/badges/', { waitUntil: 'networkidle0' }); });
await scene(r4, 'outro', async () => {
  await desk.goto(base + '/staff/', { waitUntil: 'networkidle0' });
  await desk.evaluate(() => { const h = [...document.querySelectorAll('h2')].find((e) => /milestones/i.test(e.textContent)); if (h) h.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
});
const s4 = await r4.stop();

const segments = [['prospect', 'phone', s1], ['admin', 'desk', s2], ['member', 'phone', s3], ['team', 'desk', s4]]
  .map(([name, layout, r]) => ({ name, layout, duration: r.duration, markers: r.markers, frames: r.frames }));
fs.writeFileSync(path.join(out, 'markers.json'), JSON.stringify({ segments }, null, 2));
console.log(segments.map((s) => `${s.name}: ${s.duration.toFixed(1)} s`).join(' · '));
await browser.close();
