// PNG/PDF are static; animation rectangles and source GIFs are retained for the PPTX.
// Usage from docs/pitch: node build_deck.mjs --tests 401
import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const here = path.dirname(fileURLToPath(import.meta.url));
const arg = (name,fallback) => {const i=process.argv.indexOf(`--${name}`);return i>0 ? process.argv[i+1] : fallback;};
const browser = await puppeteer.launch({executablePath:process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
try {
  const page = await browser.newPage();
  await page.setViewport({width:1920,height:1080,deviceScaleFactor:1});
  await page.goto('file://'+path.join(here,'deck.html')+'?export=1',{waitUntil:'load'});
  await page.evaluate(count => {
    document.body.innerHTML = document.body.innerHTML.replaceAll('__TESTS__',count);
    for (const image of document.querySelectorAll('[data-animation]')) image.src=image.dataset.poster;
  },arg('tests','401'));
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map(img => img.decode()));
  });
  fs.mkdirSync(path.join(here,'slides'),{recursive:true});
  const slides=await page.$$('section.slide');
  const meta=[];
  for(const [i,slide] of slides.entries()) {
    const file=`slides/slide-${String(i+1).padStart(2,'0')}.png`;
    await slide.screenshot({path:path.join(here,file)});
    const info=await slide.evaluate(el => {
      const bounds=el.getBoundingClientRect();
      const animations=[...el.querySelectorAll('[data-animation]')].map(img => {
        const box=img.getBoundingClientRect();
        return {source:img.dataset.animation,poster:img.dataset.poster,x:box.x-bounds.x,y:box.y-bounds.y,w:box.width,h:box.height,radius:parseFloat(getComputedStyle(img).borderRadius)||0};
      });
      return {id:el.dataset.script||null,seconds:Number(el.dataset.seconds)||null,notes:el.dataset.notes||'',animations};
    });
    meta.push({image:file,...info});
  }
  // Remove obsolete generated slide images after a successful capture.
  const keep=new Set(meta.map(s => path.basename(s.image)));
  for(const name of fs.readdirSync(path.join(here,'slides'))) if(/^slide-\d+\.png$/.test(name)&&!keep.has(name)) fs.unlinkSync(path.join(here,'slides',name));
  fs.writeFileSync(path.join(here,'slides/slides.json'),JSON.stringify(meta,null,2)+'\n');
  await page.pdf({path:path.join(here,'Club-des-Affaires-pitch.pdf'),width:'1920px',height:'1080px',printBackground:true});
  console.log(`${meta.length} slides, ${meta.reduce((n,s)=>n+s.animations.length,0)} GIF placements, PDF written`);
} finally {await browser.close();}
