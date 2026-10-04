// One real UI snapshot per manual slide, from an isolated demo.
import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
import path from 'node:path';
const out = process.argv[2];
if (!out) throw new Error('Usage: node capture_screens.mjs OUTPUT_DIR');
const base = process.env.BASE || 'http://127.0.0.1:8010';
const browser = await puppeteer.launch({executablePath: process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args:['--hide-scrollbars','--force-color-profile=srgb']});
const onlyIntros = process.argv.includes('--only-intros');
const onlyReferral = process.argv.includes('--only-referral');
const onlyDashboard = process.argv.includes('--only-dashboard');
const onlyBadges = process.argv.includes('--only-badges');
const manifest = onlyIntros || onlyReferral || onlyDashboard || onlyBadges ? JSON.parse(fs.readFileSync(path.join(out,'manifest.json'),'utf8')).scenes : {};
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
async function shot(page,name,label,index) {
  const frames = manifest[name] ||= [];
  const dir = path.join(out,name);
  fs.mkdirSync(dir,{recursive:true});
  const frameIndex = index ?? frames.length;
  const file = `${String(frameIndex).padStart(3,'0')}.png`;
  await page.evaluate(async () => {
    const visible = [...document.images].filter(img => {
      const rect = img.getBoundingClientRect();
      return rect.width && rect.height && rect.bottom > 0 && rect.top < innerHeight;
    });
    await Promise.all(visible.map(img => img.decode()));
  });
  await page.screenshot({path:path.join(dir,file)});
  frames[frameIndex] = {file,label,url:page.url()};
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
  if (onlyIntros) {
    if (manifest.web?.length !== 5) throw new Error('Expected the five existing web screenshots');
    const camille = await session('camille.rey@example.com');
    for (const language of ['fr','de','en']) {
      await camille.setCookie({name:'django_language',value:language,url:base});
      for (const width of [1120,390]) {
        await camille.setViewport({width,height:844,deviceScaleFactor:1.5});
        let albumPortrait;
        for (const route of ['/album/?aide=marche-alemanique','/accueil/','/evenements/4/']) {
          await go(camille,route);
          const card = await camille.waitForFunction(() => [...document.querySelectorAll('main a[href*="/membres/"]')].find(el => el.textContent.includes('Lukas Imboden')));
          await card.evaluate(el => el.scrollIntoView({block:'center'}));
          const portrait = await card.evaluate(async el => {
            const img = el.querySelector('img');
            if (!img) throw new Error('Lukas portrait missing');
            await img.decode();
            if (!img.naturalWidth) throw new Error('Lukas portrait failed to load');
            return img.getAttribute('src');
          });
          if (route.startsWith('/album/')) albumPortrait = portrait;
          else if (portrait !== albumPortrait) throw new Error(`${route}: inconsistent portrait`);
        }
        console.log(`PASS portraits: ${language}, ${width}px, album/home/event`);
      }
    }
    await camille.setViewport({width:390,height:844,deviceScaleFactor:1.5,isMobile:true,hasTouch:true});
    await go(camille,'/evenements/4/');
    await scrollTo(camille,'section h2.text-lg');
    await shot(camille,'web','Suggested introductions and synergies',4);
  } else if (onlyBadges) {
    if (![3,4].includes(manifest.admin?.length)) throw new Error('Expected the existing admin screenshots');
    const staff = await session('equipe@example.com',true);
    for (const language of ['fr','de','en']) {
      await staff.setCookie({name:'django_language',value:language,url:base});
      await go(staff,'/staff/evenements/4/badges/');
      const counts = await staff.$$eval('main section',pages => pages.map(page => page.querySelectorAll('article svg').length));
      if (JSON.stringify(counts)!==JSON.stringify([8,8,8,8,6])) throw new Error(`${language}: incorrect badge sheets`);
      if (!await staff.$('button[data-print]')) throw new Error(`${language}: missing print button`);
      console.log(`PASS badges: ${language}, 38 QR badges / five A4 sheets`);
    }
    await shot(staff,'admin','Printable QR badges for the event',3);
  } else if (onlyDashboard) {
    if (![3,4].includes(manifest.admin?.length)) throw new Error('Expected the existing admin screenshots');
    // Same point in the story as the original full capture: Camille has just met Lukas.
    const camille = await session('camille.rey@example.com');
    await go(camille,'/m/demo-lukas/');
    await Promise.all([camille.waitForNavigation({waitUntil:'networkidle0'}),camille.click('main form button[type=submit]')]);
    const staff = await session('equipe@example.com',true);
    const headings = {fr:['Rencontres enregistrées cette année','Nouveaux membres cette année'],de:['Begegnungen dieses Jahr','Neue Mitglieder dieses Jahr'],en:['Connections this year','New members this year']};
    for (const language of ['fr','de','en']) {
      await staff.setCookie({name:'django_language',value:language,url:base});
      await go(staff,'/staff/');
      const cards = await staff.$$eval('main .grid > section.card',nodes => nodes.slice(0,4).map(el => ({label:el.querySelector('p').innerText,value:el.querySelector('.text-4xl').innerText})));
      if (cards[2].value !== '181' || cards[3].value !== '6') throw new Error(`${language}: wrong annual connections or new members`);
      if (cards[2].label !== headings[language][0] || cards[3].label !== headings[language][1]) throw new Error(`${language}: ambiguous dashboard labels`);
      console.log(`PASS dashboard: ${language}, 181 annual connections / 6 new members`);
    }
    await shot(staff,'admin','Membership and meetings dashboard',0);
  } else if (onlyReferral) {
    if (manifest.referral?.length !== 3) throw new Error('Expected the three existing referral screenshots');
    const camille = await session('camille.rey@example.com');
    await go(camille,'/moi/inviter/');
    await shot(camille,'referral','A personal invitation link',0);
    await scrollTo(camille,'#invite-link');
    await shot(camille,'referral','A QR to invite a future member',1);
    const link = await camille.$eval('#invite-link',el => el.value);
    const guest = await session();
    const route = new URL(link).pathname + new URL(link).search;
    for (const language of ['fr','de','en']) {
      await guest.setCookie({name:'django_language',value:language,url:base});
      await go(guest,route);
      const fee = await guest.$eval('form .bg-stone-50',el => ({
        old:el.querySelector('s')?.innerText,new:el.querySelector('strong')?.innerText,text:el.innerText,
      }));
      if (!fee.old?.includes('500') || !fee.new?.includes('350')) throw new Error(`${language}: wrong referral fee`);
      await go(guest,new URL(link).pathname);
      if (await guest.$('form s')) throw new Error(`${language}: ordinary request received referral discount`);
      console.log(`PASS referral fee: ${language}, sponsored 350 / standard 500`);
    }
    await go(guest,route);
    await scrollTo(guest,'main .chip');
    await shot(guest,'referral','The sponsored invitation request',2);
  } else {
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
  await scrollTo(guest,'main .chip');
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
  await go(staff,'/staff/evenements/4/badges/');
  await shot(staff,'admin','Printable QR badges for the event');
  }
  fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify({scenes:manifest,errors},null,2)+'\n');
  if (errors.length) throw new Error(errors.join('\n'));
} finally {await browser.close();}
