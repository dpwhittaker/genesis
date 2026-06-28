/* The Neighbors' Stories — slide deck.
 * Flips through slides/p01.jpg … and mirrors the CURRENT SLIDE between devices
 * via /<baseurl>/sync, so a phone can drive what's on the TV. Inputs: on-screen
 * arrows, keyboard (←/→/space), and mobile swipe (LEFT = back, RIGHT = forward). */
(function () {
  'use strict';
  const TOTAL = 13;
  const SLIDES = Array.from({ length: TOTAL }, (_, i) => `slides/p${String(i + 1).padStart(2, '0')}.jpg`);
  const el = (id) => document.getElementById(id);
  const base = location.pathname.split('/sessions/')[0];   // e.g. "/genesis"
  const SYNC = base + '/sync/';

  const img = el('slide'), counter = el('counter'), link = el('link');
  let current = 0, lastSeq = -1;

  // preload every slide (the whole deck is a few MB)
  SLIDES.forEach((s) => { const im = new Image(); im.src = s; });

  function render(i) {
    current = Math.max(0, Math.min(TOTAL - 1, i));
    img.src = SLIDES[current];
    counter.textContent = (current + 1) + ' / ' + TOTAL;
  }

  // local navigation: move + push to the shared state
  function go(i) {
    i = Math.max(0, Math.min(TOTAL - 1, i));
    const changed = i !== current;
    render(i);
    if (changed) push(i);
  }
  const next = () => go(current + 1);
  const prev = () => go(current - 1);

  // ---- remote drive (sync just the current slide) ----
  function setLinked(ok) { if (link) link.classList.toggle('on', ok); }
  async function push(i) {
    try {
      const r = await fetch(SYNC + 'goto', {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ slide: i, total: TOTAL }),
      });
      lastSeq = (await r.json()).seq; setLinked(true);
    } catch (_) { setLinked(false); }
  }
  async function poll() {
    try {
      const s = await (await fetch(SYNC + 'state', { cache: 'no-store' })).json();
      setLinked(true);
      if (s.seq > lastSeq) { lastSeq = s.seq; if (s.slide !== current) render(s.slide); }
    } catch (_) { setLinked(false); }
    setTimeout(poll, 700);
  }
  async function init() {
    try {                                   // adopt the screen's current slide (late-join)
      const s = await (await fetch(SYNC + 'state', { cache: 'no-store' })).json();
      lastSeq = s.seq; render(s.total ? s.slide : 0); setLinked(true);
    } catch (_) { render(0); setLinked(false); }
    poll();
  }

  // ---- input ----
  el('prev').onclick = prev;
  el('next').onclick = next;
  el('full').onclick = toggleFull;
  document.addEventListener('keydown', (e) => {
    const k = e.key;
    if (k === 'ArrowRight' || k === ' ' || k === 'PageDown') { e.preventDefault(); next(); }
    else if (k === 'ArrowLeft' || k === 'PageUp') { e.preventDefault(); prev(); }
    else if (k.toLowerCase() === 'f') toggleFull();
  });

  // swipe — LEFT goes back, RIGHT goes forward (per the brief)
  let sx = 0, sy = 0, st = 0;
  const app = el('app');
  app.addEventListener('touchstart', (e) => { const t = e.changedTouches[0]; sx = t.clientX; sy = t.clientY; st = Date.now(); }, { passive: true });
  app.addEventListener('touchend', (e) => {
    const t = e.changedTouches[0], dx = t.clientX - sx, dy = t.clientY - sy;
    if (Date.now() - st < 800 && Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy) * 1.3) {
      if (dx < 0) prev(); else next();
    }
  }, { passive: true });

  function toggleFull() {
    if (!document.fullscreenElement) (document.documentElement.requestFullscreen || (() => {})).call(document.documentElement);
    else (document.exitFullscreen || (() => {})).call(document);
  }

  init();
})();
