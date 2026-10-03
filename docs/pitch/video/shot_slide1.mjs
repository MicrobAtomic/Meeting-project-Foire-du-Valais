// Picture of slide 1: the album (default) or the public home page, phone size, in English, without the demo banner
// (the server must run with DEMO_BANNER=0). Usage: BASE=http://127.0.0.1:8010 node shot_slide1.mjs OUT.png [album|landing]
import puppeteer from 'puppeteer-core';

const base = process.env.BASE || 'http://127.0.0.1:8010';
const [out, which = 'album'] = process.argv.slice(2);
const browser = await puppeteer.launch({ executablePath: process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--hide-scrollbars'] });
const page = await browser.newPage();
await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
await page.setCookie({ name: 'django_language', value: 'en', url: base });
if (which === 'album') {
  await page.goto(base + '/connexion/', { waitUntil: 'networkidle0' });
  await page.type('#id_username', 'camille.rey@example.com');
  await page.type('#id_password', 'club-demo-2026');
  await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle0' }), page.click('main form button[type=submit]')]);
  await page.goto(base + '/album/', { waitUntil: 'networkidle0' });
  // start on the first card with a portrait, not on the filter form
  await page.evaluate(() => {
    const photo = document.querySelector('main a[href*="/membres/"] img');
    const card = photo ? photo.closest('a') : document.querySelector('main a[href*="/membres/"]');
    if (card) { card.scrollIntoView({ block: 'start' }); window.scrollBy(0, -72); }
  });
} else {
  await page.goto(base + '/', { waitUntil: 'networkidle0' });
}
await page.screenshot({ path: out });
await browser.close();
