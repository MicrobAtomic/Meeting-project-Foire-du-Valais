// One real UI snapshot per manual slide. No app/template changes.
import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
import path from 'node:path';
const out = process.argv[2];
if (!out) throw new Error('Usage: node capture_screens.mjs OUTPUT_DIR');
const base = process.env.BASE || 'http://127.0.0.1:8010';
const browser = await puppeteer.launch({executablePath: process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args:['--hide-scrollbars','--force-color-profile=srgb']});
const manifest = {};
const errors = [];
const pause = ms => new Promise(r => setTimeout(r, ms));
async function session(email, desktop = false) {
  const context = await browser.createBrowserContext();
  const page = await context.newPage();
  await page.setViewport(desktop ? {width:1120,height:700,deviceScaleFactor:1} : {width:390,height:844,deviceScaleFactor:1.5,isMobile:true,hasTouch:true});
  await page.setCookie({name:'django_language',value:'en',url:base});
  page.on('pageerror', e => errors.push(e.message));
  if (email) await login(page,email);
  return page;
}
async function go(page, route) {
  const response = await page.goto(base + route,{waitUntil:'networkidle0'});
  if (!response?.ok()) throw new Error(`${route}: HTTP ${response?.status()}`);
  await page.evaluate(() => document.fonts.ready);
}
async function login(page,email) {
  await go(page,'/connexion/');
  await page.type('#id_username',email);
  await page.type('#id_password','club-demo-2026');
  await Promise.all([page.waitForNavigation({waitUntil:'networkidle0'}),page.click('main form button[type=submit]')]);
  if (new URL(page.url()).pathname === '/connexion/') throw new Error('Demo login failed');
}
async function shot(page,name,label) {
  const frames = manifest[name] ||= [];
  const dir = path.join(out,name);
  fs.mkdirSync(dir,{recursive:true});
  const file = `${String(frames.length).padStart(3,'0')}.png`;
  await page.screenshot({path:path.join(dir,file)});
  frames.push({file,label,url:page.url()});
  console.log(`${name}: ${label}`);
}
async function scrollTo(page,selector,block='start') {
  await page.$eval(selector,(el,b) => {el.scrollIntoView({block:b});if(b==='start') window.scrollBy(0,-84);},block);
  await pause(150);
}
async function clickText(page,selector,text) {
  const handle = await page.waitForFunction((sel,txt) => [...document.querySelectorAll(sel)].find(el => el.textContent.includes(txt)),{},selector,text);
  const el = handle.asElement();
  await el.evaluate(node => node.scrollIntoView({block:'center'}));
  await Promise.all([page.waitForNavigation({waitUntil:'networkidle0'}),el.click()]);
}
try {
  const camille = await session();
  await go(camille,'/');
  await shot(camille,'web','Public home');
  await go(camille,'/connexion/');
  await camille.type('#id_username','camille.rey@example.com');
  await camille.type('#id_password','club-demo-2026');
  await shot(camille,'web','Member login');
  await Promise.all([camille.waitForNavigation({waitUntil:'networkidle0'}),camille.click('main form button[type=submit]')]);
  await go(camille,'/accueil/');
  await shot(camille,'web','Camille dashboard before her meeting');
  await go(camille,'/album/?aide=marche-alemanique');
  const card = await camille.waitForFunction(() => [...document.querySelectorAll('main a[href*="/membres/"]')].find(el => el.textContent.includes('Lukas Imboden')));
  await card.evaluate(el => {el.scrollIntoView({block:'start'});window.scrollBy(0,-84);});
  await shot(camille,'web','Lukas in the filtered album');
  await go(camille,'/evenements/4/');
  await scrollTo(camille,'section h2.text-lg');
  await shot(camille,'web','Suggested introductions and synergies');

  const lukas = await session('lukas.imboden@example.com');
  await go(lukas,'/moi/qr/');
  await shot(lukas,'event','Lukas shows his QR badge');
  await go(camille,'/m/demo-lukas/');
  await shot(camille,'event','Camille confirms the meeting');
  await Promise.all([camille.waitForNavigation({waitUntil:'networkidle0'}),camille.click('main form button[type=submit]')]);
  await scrollTo(camille,'main');
  await shot(camille,'event','The card joins the album');
  await camille.$eval('main a[href^="mailto:"]', el => el.closest('section').scrollIntoView({block:'center'}));
  await shot(camille,'event','Contact details unlock');
  await go(camille,'/evenements/4/bingo/');
  await scrollTo(camille,'main ol','center');
  await shot(camille,'event','One real encounter ticks one square');
  const bingoText = await camille.$eval('main',el => el.innerText);
  if (!bingoText.includes('Lukas')) throw new Error('Bingo did not register Lukas');

  await go(camille,'/moi/inviter/');
  await shot(camille,'referral','A personal invitation link');
  await scrollTo(camille,'#invite-link');
  await shot(camille,'referral','A QR to invite a future member');
  const link = await camille.$eval('#invite-link',el => el.value);
  const guest = await session();
  await go(guest,new URL(link).pathname + new URL(link).search);
  await shot(guest,'referral','The sponsored invitation request');

  const staff = await session('equipe@example.com',true);
  await go(staff,'/staff/');
  await shot(staff,'admin','Membership and meetings dashboard');
  await go(staff,'/staff/evenements/4/');
  const button = await staff.waitForFunction(() => [...document.querySelectorAll('button')].find(el => el.textContent.includes('Generate the seating plan')));
  await button.evaluate(el => el.scrollIntoView({block:'center'}));
  await shot(staff,'admin','Prepare the event with one action');
  await clickText(staff,'button','Generate the seating plan');
  // Include the plan heading and statistics, not the unrelated list of suggested introductions.
  await staff.evaluate(() => {
    const firstRound = document.querySelector('section.break-inside-avoid');
    if (!firstRound) throw new Error('No generated seating plan');
    firstRound.parentElement.scrollIntoView({block:'start'});
    window.scrollBy(0,-84);
  });
  await shot(staff,'admin','Rotating tables for 38 guests');
  fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify({scenes:manifest,errors},null,2)+'\n');
  if (errors.length) throw new Error(errors.join('\n'));
} finally {await browser.close();}
