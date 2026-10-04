// Shared chapter template + screen-by-screen script -> static deck, PNGs, PDF and PPTX metadata.
// Usage from docs/pitch: node build_deck.mjs --tests 403
import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
const arg=(name,fallback)=>{const i=process.argv.indexOf(`--${name}`);return i>0?process.argv[i+1]:fallback;};
const story=JSON.parse(fs.readFileSync(path.join(here,'story.json'),'utf8'));
const browser=await puppeteer.launch({executablePath:process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
try {
 const page=await browser.newPage();
 await page.setViewport({width:1920,height:1080,deviceScaleFactor:1});
 await page.goto('file://'+path.join(here,'template.html')+'?export=1',{waitUntil:'load'});
 await page.evaluate((story,count)=>{
  const templates=new Map([...document.querySelectorAll('section[data-chapter]')].map(el=>[el.dataset.chapter,el]));
  const appendices=[...document.querySelectorAll('section.slide')].filter(el=>!el.dataset.chapter);
  const player=document.querySelector('script[src="presenter.js"]');
  const time=t=>`${Math.floor(t/60)}:${String(t%60).padStart(2,'0')}`;
  const main=story.map((row,index)=>{
   const template=templates.get(row.chapter);
   if(!template)throw new Error(`Missing chapter ${row.chapter}`);
   const slide=template.cloneNode(true);
   slide.dataset.script=row.id;
   slide.dataset.seconds=row.seconds;
   slide.dataset.notes=`(${time(row.start)}–${time(row.end)}) ${row.text}`;
   const image=slide.querySelector('[data-screen]');
   if(Boolean(image)!==Boolean(row.screen))throw new Error(`Screen/template mismatch: ${row.id}`);
   if(image){image.dataset.screen=row.screen;image.src=row.screen;image.alt=row.label;}
   slide.querySelector('[data-slide-index]').textContent=`${index+1} / ${story.length}`;
   return slide;
  });
  document.body.replaceChildren(...main,...appendices,player);
  document.body.innerHTML=document.body.innerHTML.replaceAll('__TESTS__',count);
 },story,arg('tests','403'));
 await page.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(img=>img.decode()));});
 fs.writeFileSync(path.join(here,'deck.html'),'<!doctype html>\n'+await page.evaluate(()=>document.documentElement.outerHTML)+'\n');
 fs.mkdirSync(path.join(here,'slides'),{recursive:true});
 const slides=await page.$$('section.slide');
 const meta=[];
 for(const [i,slide] of slides.entries()) {
  const file=`slides/slide-${String(i+1).padStart(2,'0')}.png`;
  await slide.screenshot({path:path.join(here,file)});
  const info=await slide.evaluate(el=>{
   const bounds=el.getBoundingClientRect();
   const screens=[...el.querySelectorAll('[data-screen]')].map(img=>{
    const box=img.getBoundingClientRect();
    return {source:img.dataset.screen,x:box.x-bounds.x,y:box.y-bounds.y,w:box.width,h:box.height};
   });
   return {id:el.dataset.script||null,chapter:el.dataset.chapter||null,seconds:Number(el.dataset.seconds)||null,notes:el.dataset.notes||'',screens};
  });
  meta.push({image:file,...info});
 }
 const keep=new Set(meta.map(s=>path.basename(s.image)));
 for(const name of fs.readdirSync(path.join(here,'slides')))if(/^slide-\d+\.png$/.test(name)&&!keep.has(name))fs.unlinkSync(path.join(here,'slides',name));
 fs.writeFileSync(path.join(here,'slides/slides.json'),JSON.stringify(meta,null,2)+'\n');
 await page.pdf({path:path.join(here,'Club-des-Affaires-pitch.pdf'),width:'1920px',height:'1080px',printBackground:true});
 console.log(`${story.length} main slides, ${meta.length} PDF pages, ${meta.reduce((n,s)=>n+s.screens.length,0)} fixed screens`);
} finally {await browser.close();}
