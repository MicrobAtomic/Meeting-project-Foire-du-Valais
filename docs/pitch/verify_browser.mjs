// Checks slide layout, offline navigation and real GIF playback in Chrome.
import puppeteer from 'puppeteer-core';
import path from 'node:path';
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
const browser=await puppeteer.launch({executablePath:process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
const pause=ms=>new Promise(r=>setTimeout(r,ms));
try {
 const page=await browser.newPage();
 const failures=[];
 page.on('pageerror',e=>failures.push(e.message));
 page.on('request',request=>{if(/^https?:/.test(request.url()))failures.push('External request: '+request.url());});
 await page.setViewport({width:1920,height:1080});
 const url='file://'+path.join(here,'deck.html');
 await page.goto(url+'?export=1',{waitUntil:'load'});
 await page.evaluate(async()=>{for(const img of document.querySelectorAll('[data-animation]'))img.src=img.dataset.poster;await document.fonts.ready;await Promise.all([...document.images].map(img=>img.decode()));});
 const layout=await page.evaluate(()=>{
  const cropped=[],overlaps=[];
  for(const [i,slide] of [...document.querySelectorAll('section.slide')].entries()){
   const s=slide.getBoundingClientRect();
   const media=[...slide.querySelectorAll('[data-animation]')].map(img=>img.getBoundingClientRect());
   const walker=document.createTreeWalker(slide,NodeFilter.SHOW_TEXT);
   while(walker.nextNode()){
    const node=walker.currentNode;if(!node.textContent.trim())continue;
    const range=document.createRange();range.selectNodeContents(node);
    for(const r of range.getClientRects()){
     if(r.x<s.x-1||r.y<s.y-1||r.right>s.right+1||r.bottom>s.bottom+1)cropped.push({slide:i+1,text:node.textContent.trim()});
     if(media.some(m=>r.x<m.right&&r.right>m.x&&r.y<m.bottom&&r.bottom>m.y))overlaps.push({slide:i+1,text:node.textContent.trim()});
    }
   }
  }
  return {slides:document.querySelectorAll('section.slide').length,main:document.querySelectorAll('[data-script]').length,annexes:document.querySelectorAll('.appendix').length,cropped,overlaps};
 });
 assert.equal(layout.slides,15);assert.equal(layout.main,7);assert.equal(layout.annexes,7);
 assert.deepEqual(layout.cropped,[]);assert.deepEqual(layout.overlaps,[]);
 await page.goto(url,{waitUntil:'load'});
 const current=()=>page.$eval('.slide.current',s=>s.dataset.script||'appendix');
 assert.equal(await current(),'intro');
 await page.keyboard.press('ArrowRight');assert.equal(await current(),'problem');
 await page.keyboard.press('ArrowRight');assert.equal(await current(),'web');
 await pause(500);
 const frame1=await (await page.$('.current [data-animation]')).screenshot();
 await pause(5000);
 const frame2=await (await page.$('.current [data-animation]')).screenshot();
 assert(!Buffer.from(frame1).equals(Buffer.from(frame2)),'GIF must animate in the offline presentation');
 await page.keyboard.press('r');
 await pause(500);
 const restarted=await (await page.$('.current [data-animation]')).screenshot();
 assert(Buffer.from(frame1).equals(Buffer.from(restarted)),'Replay must return to the first GIF frame');
 await page.keyboard.press('n');assert(await page.$('.presenter-notes.visible'));
 await page.keyboard.press('n');
 await page.keyboard.press('End');assert.equal(await current(),'closing');
 await page.keyboard.press('ArrowRight');assert.equal(await current(),'closing','Stop before the appendices');
 await page.keyboard.press('a');assert.equal(await current(),'appendix');
 await page.keyboard.press('ArrowRight');assert.equal(await current(),'appendix');
 await page.keyboard.press('a');assert.equal(await current(),'closing');
 await page.keyboard.press('Home');assert.equal(await current(),'intro');
 await page.setViewport({width:1280,height:720});
 await pause(200);
 const size=await page.$eval('.current',el=>{const r=el.getBoundingClientRect();return [Math.round(r.width),Math.round(r.height)];});
 assert.deepEqual(size,[1280,720]);
 assert.deepEqual(failures,[]);
 fs.mkdirSync(path.join(here,'.build'),{recursive:true});
 fs.writeFileSync(path.join(here,'.build/browser-check.json'),JSON.stringify({...layout,offlinePlayback:true,navigation:true},null,2)+'\n');
 console.log('PASS: 15 slides, no cropped/overlapping text, offline GIF playback, manual navigation, notes, Q&A, viewport resize.');
} finally {await browser.close();}
