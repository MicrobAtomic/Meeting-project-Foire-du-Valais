// Offline presentation. Export tools use ?export=1 to keep every slide visible.
(() => {
  const params = new URLSearchParams(location.search);
  document.body.innerHTML = document.body.innerHTML.replaceAll('__TESTS__', '401');
  if (params.has('export')) return;
  const slides = [...document.querySelectorAll('section.slide')];
  const mainCount = slides.filter(slide => slide.dataset.script).length;
  const css = document.createElement('style');
  css.textContent = `body.presenting{overflow:hidden;background:#1c1917}body.presenting .slide{display:none;position:absolute;transform-origin:top left}body.presenting .slide.current{display:flex}.presenter-controls{position:fixed;bottom:8px;left:50%;transform:translateX(-50%);z-index:9999;background:#1c1917ee;color:#fafaf9;padding:8px 16px;border-radius:12px;font-size:14px;display:flex;align-items:center;gap:16px}.presenter-controls button{border:1px solid #78716c;background:#292524;color:white;border-radius:6px;padding:6px 12px;font:inherit;cursor:pointer}.presenter-notes{display:none;position:fixed;bottom:65px;left:10%;right:10%;background:#fff;color:#1c1917;border:2px solid #b91c1c;border-radius:16px;padding:24px;font-size:21px;line-height:1.5;z-index:9998}.presenter-notes.visible{display:block}@media print{.presenter-controls,.presenter-notes{display:none}}`;
  document.head.append(css);
  const controls = document.createElement('nav');
  controls.className = 'presenter-controls';
  controls.setAttribute('aria-label','Presentation controls');
  controls.innerHTML = '<button data-action="back" aria-label="Previous slide">←</button><span></span><button data-action="next" aria-label="Next slide">→</button><button data-action="replay">Replay GIF · R</button><button data-action="notes">Notes · N</button><button data-action="appendix">Q&amp;A · A</button><button data-action="fullscreen">Fullscreen · F</button>';
  const notes = document.createElement('aside');
  notes.className = 'presenter-notes';
  document.body.append(controls,notes);
  document.body.classList.add('presenting');
  let index = 0;
  function replay() {
    for (const img of slides[index].querySelectorAll('[data-animation]')) {
      // Clone creates a new image decoder, starting this GIF when this slide becomes visible.
      const replacement = img.cloneNode();
      replacement.src = img.dataset.animation + '?replay=' + Date.now();
      img.replaceWith(replacement);
    }
  }
  function layout() {
    const scale = Math.min(innerWidth/1920,innerHeight/1080);
    slides[index].style.transform = `scale(${scale})`;
    slides[index].style.left = `${(innerWidth-1920*scale)/2}px`;
    slides[index].style.top = `${(innerHeight-1080*scale)/2}px`;
  }
  function show(next) {
    const max = index < mainCount && next >= mainCount ? mainCount-1 : slides.length-1;
    index = Math.max(0,Math.min(next,max));
    slides.forEach((slide,i) => slide.classList.toggle('current',i===index));
    controls.querySelector('span').textContent = index < mainCount ? `${index+1}/${mainCount} · manual timing` : `Q&A ${index-mainCount}/${slides.length-mainCount-1}`;
    notes.textContent = slides[index].dataset.notes;
    replay(); layout();
  }
  function action(name) {
    if (name === 'next') show(index+1);
    if (name === 'back') show(index-1);
    if (name === 'replay') replay();
    if (name === 'notes') notes.classList.toggle('visible');
    if (name === 'appendix') { index = index < mainCount ? mainCount : mainCount-1; show(index); }
    if (name === 'fullscreen') {
      const operation = document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
      operation?.catch(() => {});
    }
  }
  controls.addEventListener('click',e => action(e.target.closest('button')?.dataset.action));
  document.addEventListener('keydown',e => {
    if (['ArrowRight',' ','PageDown'].includes(e.key)) {e.preventDefault();action('next');}
    if (['ArrowLeft','PageUp'].includes(e.key)) {e.preventDefault();action('back');}
    if (e.key === 'Home') show(0);
    if (e.key === 'End') {index=mainCount-1;show(index);}
    const names = {r:'replay',n:'notes',a:'appendix',f:'fullscreen'};
    if (names[e.key.toLowerCase()]) action(names[e.key.toLowerCase()]);
  });
  addEventListener('resize',layout);
  let hideTimer;
  function revealControls() {
    controls.classList.remove('quiet');
    clearTimeout(hideTimer);
    hideTimer=setTimeout(() => controls.classList.add('quiet'),2500);
  }
  css.textContent += '.presenter-controls.quiet:not(:focus-within){opacity:0;pointer-events:none}';
  document.addEventListener('mousemove',revealControls);
  revealControls();
  show(0);
})();
