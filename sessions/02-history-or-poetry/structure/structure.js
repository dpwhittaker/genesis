/* The Shape of Genesis 1 — stepped structure animation.
 * A guided walk: envelope -> forming/filling (ABCABC) -> chiasm (ABCCBA) ->
 * word-count center (moadim) -> human climax internals -> the lone line ->
 * convergence. Navigation + remote sync mirror the session-1 slideshow. */
(function () {
  'use strict';
  const el = (id) => document.getElementById(id);
  const stage = el('stage'), linesSvg = el('lines');
  const base = location.pathname.split('/sessions/')[0];   // e.g. "/genesis"
  const SYNC = base + '/sync/';

  /* ---- block catalogue (intrinsic kind + label + Hebrew word count) ---- */
  const B = {
    A:   { kind: 'frame',  t: 'A · 1:1',  bs: 'the heavens and the earth', wc: 7 },
    Bx:  { kind: 'frame',  t: 'B · 1:2',  bs: 'unformed and void', wc: 14 },
    d1:  { kind: '',       t: 'Day 1 · light', bs: '', wc: 25 },
    d2:  { kind: '',       t: 'Day 2 · sky & seas', bs: '', wc: 32 },
    d3:  { kind: '',       t: 'Day 3 · dry land', bs: '', wc: 63 },
    d4:  { kind: 'center', t: 'Day 4 · lights ✦', bs: '', wc: 63 },
    d5:  { kind: '',       t: 'Day 5 · fish & birds', bs: '', wc: 51 },
    d6a: { kind: '',       t: 'Day 6a · animals', bs: '', wc: 32 },
    hum: { kind: 'human',  t: 'Day 6b · humankind', bs: 'a 111-word climax', wc: 111 },
    Bp:  { kind: 'frame',  t: 'B′ · 2:1', bs: '…were finished', wc: 5 },
    Ap:  { kind: 'goal',   t: 'A′ · 2:2-3', bs: 'rested · blessed · hallowed', wc: 30 },
    huC:  { kind: 'cl-c',   t: 'C · v26 · dominion (plan)', bs: '' },
    huP:  { kind: 'poem',   t: 'v27 · image of God ×3', bs: 'the first poetry' },
    huCp: { kind: 'cl-c',   t: "C′ · v28 · dominion (blessing)", bs: '' },
    huD:  { kind: 'cl-d',   t: 'D · v29 · food → humankind', bs: '' },
    huDp: { kind: 'cl-d',   t: "D′ · v30 · food → animals", bs: '' },
    huS:  { kind: 'beacon', t: '★ v31 · and it was very good', bs: '' },
  };
  // build DOM nodes
  const node = {};
  for (const id in B) {
    const d = document.createElement('div');
    d.className = 'block ' + B[id].kind;
    d.innerHTML = `<div class="brow"><span class="bt">${B[id].t}</span>` +
      (B[id].wc ? `<span class="wc">${B[id].wc}</span>` : '') + `</div>` +
      (B[id].bs ? `<span class="bs">${B[id].bs}</span>` : '');
    stage.appendChild(d);
    node[id] = d;
  }

  const cx = (w) => Math.round(500 - w / 2);
  const wpx = (w) => Math.round(150 + w * 4);   // word count -> box width for the hill

  /* ---- step layouts ---------------------------------------------------
   * Each step: { cap, title?, center?, final?, blocks:{id:{x,y,w,h,cls,wc}}, lines:[...] }
   * blocks omitted from a step fade out. line = ['line',x1,y1,x2,y2,cls] | ['path',d,cls] */
  const W = 540;
  const STEPS = [
    { // 0 — title
      card: 'title',
      cap: 'Genesis 1 is one of the most tightly built passages in the Bible. Step through its shape. <i>→ or space to advance.</i>',
      blocks: {},
    },
    { // 1 — the envelope
      cap: 'An <b>envelope</b>. It opens on "the heavens and the earth" (<b>A</b>, seven words) and closes on God\'s rest (<b>A′</b>). Just inside sit the problem — "unformed and void" (<b>B</b>) — and its answer, "finished" (<b>B′</b>).',
      blocks: {
        A:  { x: cx(W), y: 92,  w: W, h: 78 },
        Bx: { x: cx(W), y: 178, w: W, h: 78 },
        Bp: { x: cx(W), y: 392, w: W, h: 74 },
        Ap: { x: cx(W), y: 474, w: W, h: 86 },
      },
    },
    { // 2 — separating / the void
      cap: 'Pull the frame apart and a void opens between them — <b>tohu va-vohu</b>, no shape and no content. Six days will supply both.',
      blocks: {
        A:  { x: cx(W), y: 44,  w: W, h: 76 },
        Bx: { x: cx(W), y: 128, w: W, h: 76 },
        Bp: { x: cx(W), y: 452, w: W, h: 72 },
        Ap: { x: cx(W), y: 532, w: W, h: 84 },
      },
    },
    { // 3 — forming / filling (ABCABC)
      cap: 'Days 1–3 <b>form</b>; Days 4–6 <b>fill</b>. Day 1 makes light → Day 4 fills it; Day 2 parts sky and sea → Day 5 fills them; Day 3 brings dry land → Day 6 fills it. <b>A·B·C ‖ A·B·C.</b>',
      blocks: {
        A:  { x: 250, y: 14,  w: 500, h: 40, cls: 'lid' },
        Bx: { x: 250, y: 58,  w: 500, h: 40, cls: 'lid' },
        d1:  { x: 80,  y: 118, w: 400, h: 66, cls: 'pairA' },
        d2:  { x: 80,  y: 198, w: 400, h: 66, cls: 'pairB' },
        d3:  { x: 80,  y: 278, w: 400, h: 66, cls: 'pairC' },
        d4:  { x: 520, y: 118, w: 400, h: 66, cls: 'pairA' },
        d5:  { x: 520, y: 198, w: 400, h: 66, cls: 'pairB' },
        d6a: { x: 520, y: 278, w: 400, h: 66, cls: 'pairC' },
        Bp: { x: 250, y: 452, w: 500, h: 40, cls: 'lid' },
        Ap: { x: 250, y: 496, w: 500, h: 40, cls: 'lid' },
      },
      lines: [
        ['line', 480, 151, 520, 151, 'par'],
        ['line', 480, 231, 520, 231, 'par'],
        ['line', 480, 311, 520, 311, 'par'],
      ],
    },
    { // 4 — Day 6 splits 6a / 6b
      cap: 'Day 6 carries a double load. The animals (<b>6a</b>) finish the sixth panel — but humankind (<b>6b</b>) is heaped on top, <i>outside</i> the six-fold pattern. Set it aside, and six clean panels remain.',
      blocks: {
        A:  { x: 250, y: 14,  w: 500, h: 40, cls: 'lid' },
        Bx: { x: 250, y: 58,  w: 500, h: 40, cls: 'lid' },
        d1:  { x: 80,  y: 110, w: 400, h: 62, cls: 'pairA' },
        d2:  { x: 80,  y: 186, w: 400, h: 62, cls: 'pairB' },
        d3:  { x: 80,  y: 262, w: 400, h: 62, cls: 'pairC' },
        d4:  { x: 520, y: 110, w: 400, h: 58, cls: 'pairA' },
        d5:  { x: 520, y: 186, w: 400, h: 58, cls: 'pairB' },
        d6a: { x: 520, y: 262, w: 400, h: 54, cls: 'pairC' },
        hum: { x: 542, y: 330, w: 400, h: 74 },
        Bp: { x: 250, y: 452, w: 500, h: 40, cls: 'lid' },
        Ap: { x: 250, y: 496, w: 500, h: 40, cls: 'lid' },
      },
      lines: [
        ['line', 480, 141, 520, 139, 'par'],
        ['line', 480, 217, 520, 215, 'par'],
        ['line', 480, 293, 520, 289, 'par'],
        ['path', 'M720 316 C 736 324 752 326 768 330', 'split'],
      ],
    },
    { // 5 — the chiasm hill (ABCCBA by word count)
      cap: 'Now read the six by <b>length</b>: 25 · 32 · <b>63 ‖ 63</b> · 51 · 32. They fold into a hill — small, medium, large mirrored by large, medium, small. The two at the summit are <b>exactly equal: 63 = 63</b>.',
      blocks: {
        d1:  { x: cx(wpx(25)), y: 96,  w: wpx(25), h: 64, cls: 'show-wc', t: 'Day 1' },
        d2:  { x: cx(wpx(32)), y: 168, w: wpx(32), h: 64, cls: 'show-wc', t: 'Day 2' },
        d3:  { x: cx(wpx(63)), y: 240, w: wpx(63), h: 64, cls: 'show-wc summit', t: 'Day 3' },
        d4:  { x: cx(wpx(63)), y: 312, w: wpx(63), h: 64, cls: 'show-wc summit', t: 'Day 4 ✦' },
        d5:  { x: cx(wpx(51)), y: 384, w: wpx(51), h: 64, cls: 'show-wc', t: 'Day 5' },
        d6a: { x: cx(wpx(32)), y: 456, w: wpx(32), h: 64, cls: 'show-wc', t: 'Day 6a' },
      },
      lines: [
        ['path', 'M290 128 C 196 128 196 488 290 488', 'fold'],
        ['path', 'M290 200 C 224 200 224 416 290 416', 'fold'],
        ['path', 'M290 272 C 258 272 258 344 290 344', 'fold'],
      ],
    },
    { // 6 — the center word: moadim
      card: 'centerCard',
      cap: 'Lift the "evening and morning" refrains out as the <b>seams</b> they are, and the six panels run <b>266 Hebrew words</b>. Their exact center falls between "for signs" and "for seasons" — <b>mōʿăḏîm</b>, sacred time. The hinge word on the hinge.',
      blocks: {
        d1:  { x: cx(wpx(25)), y: 96,  w: wpx(25), h: 64, cls: 'dim show-wc', t: 'Day 1' },
        d2:  { x: cx(wpx(32)), y: 168, w: wpx(32), h: 64, cls: 'dim show-wc', t: 'Day 2' },
        d3:  { x: cx(wpx(63)), y: 240, w: wpx(63), h: 64, cls: 'show-wc summit', t: 'Day 3' },
        d4:  { x: cx(wpx(63)), y: 312, w: wpx(63), h: 64, cls: 'show-wc pulse-wc summit', t: 'Day 4 ✦' },
        d5:  { x: cx(wpx(51)), y: 384, w: wpx(51), h: 64, cls: 'dim show-wc', t: 'Day 5' },
        d6a: { x: cx(wpx(32)), y: 456, w: wpx(32), h: 64, cls: 'dim show-wc', t: 'Day 6a' },
      },
      lines: [
        ['line', 110, 308, 206, 308, 'fold'],
        ['line', 794, 308, 890, 308, 'fold'],
      ],
    },
    { // 7 — the human climax, internal parallels
      cap: 'The climax has its own shape. A <b>dominion frame</b> — C (the plan), C′ (the blessing) — wraps the Bible\'s <b>first poetry</b> (v.27, folding on "the image of God"). Then a matched couplet on <b>food</b>: D to humankind, D′ to the animals.',
      blocks: {
        huC:  { x: 210, y: 72,  w: 580, h: 56 },
        huP:  { x: 300, y: 136, w: 400, h: 74 },
        huCp: { x: 210, y: 218, w: 580, h: 56 },
        huD:  { x: 210, y: 292, w: 580, h: 56 },
        huDp: { x: 210, y: 356, w: 580, h: 56 },
        huS:  { x: 210, y: 432, w: 580, h: 62 },
      },
      lines: [
        ['path', 'M200 100 C 156 100 156 246 200 246', 'brace'],
        ['path', 'M200 320 C 166 320 166 384 200 384', 'brace'],
      ],
    },
    { // 8 — the single unpaired line
      cap: 'One line has no partner — not the dominion, not the food, not the poem, but verse 31: <i>"and behold, it was very good."</i> The <b>single unpaired line</b> in the whole composition, the capstone over it all.',
      blocks: {
        huC:  { x: 210, y: 72,  w: 580, h: 56, cls: 'dim' },
        huP:  { x: 300, y: 136, w: 400, h: 74, cls: 'dim' },
        huCp: { x: 210, y: 218, w: 580, h: 56, cls: 'dim' },
        huD:  { x: 210, y: 292, w: 580, h: 56, cls: 'dim' },
        huDp: { x: 210, y: 356, w: 580, h: 56, cls: 'dim' },
        huS:  { x: 200, y: 300, w: 600, h: 92, cls: 'glow' },
      },
    },
    { // 9 — the claim: a good world God upholds
      card: 'finalCard',
      cap: 'Three witnesses, one point — the frame, the center, the lone line. <i>Genesis 1:31 · Colossians 1:17 — in him all things hold together.</i>',
      blocks: {},
    },
    { // 10 — rest is the ancient lesson of trust
      card: 'close2',
      cap: '<i>Genesis 15:6 · Deuteronomy 5:15 — remember that you were slaves in Egypt.</i>',
      blocks: {},
    },
    { // 11 — the modern masters, and the question
      card: 'close3',
      cap: '<i>Exodus 20:8–11 · Matthew 11:28 — come to me, all who are weary.</i>',
      blocks: {},
    },
  ];

  /* ---- rendering ------------------------------------------------------ */
  function ns(tag) { return document.createElementNS('http://www.w3.org/2000/svg', tag); }
  function drawLines(lines) {
    linesSvg.innerHTML =
      '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">' +
      '<path d="M0 0 L10 5 L0 10 z" fill="#3f6f9f"/></marker></defs>';
    (lines || []).forEach((L) => {
      let e;
      if (L[0] === 'line') { e = ns('line'); e.setAttribute('x1', L[1]); e.setAttribute('y1', L[2]); e.setAttribute('x2', L[3]); e.setAttribute('y2', L[4]); e.setAttribute('class', 'ln ' + L[5]); }
      else { e = ns('path'); e.setAttribute('d', L[1]); e.setAttribute('class', 'ln ' + L[2]); }
      linesSvg.appendChild(e);
    });
  }

  function apply(step) {
    const S = STEPS[step];
    // blocks
    for (const id in node) {
      const b = S.blocks[id];
      const n = node[id];
      if (b) {
        n.style.left = b.x + 'px'; n.style.top = b.y + 'px';
        n.style.width = b.w + 'px'; n.style.height = b.h + 'px';
        n.style.opacity = '1';
        n.className = 'block ' + B[id].kind + (b.cls ? ' ' + b.cls : '');
        n.querySelector('.bt').textContent = b.t || B[id].t;   // per-step label override
      } else {
        n.style.opacity = '0';
        n.className = 'block ' + B[id].kind;   // drop dim/glow so opacity:0 isn't overridden by !important
      }
    }
    drawLines(S.lines);
    el('caption').innerHTML = S.cap || '';
    ['title', 'centerCard', 'finalCard', 'close2', 'close3'].forEach((id) => el(id).classList.toggle('on', S.card === id));
    el('counter').textContent = (step + 1) + ' / ' + STEPS.length;
  }

  /* ---- navigation + remote sync (mirrors session-1 slideshow) --------- */
  let current = 0, lastSeq = -1;
  function render(i) { current = Math.max(0, Math.min(STEPS.length - 1, i)); apply(current); }
  function go(i) {
    i = Math.max(0, Math.min(STEPS.length - 1, i));
    const changed = i !== current; render(i); if (changed) push(i);
  }
  const next = () => go(current + 1);
  const prev = () => go(current - 1);

  function setLinked(ok) { const l = el('link'); if (l) l.classList.toggle('on', ok); }
  async function push(i) {
    try {
      const r = await fetch(SYNC + 'goto', {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ slide: i, total: STEPS.length }),
      });
      lastSeq = (await r.json()).seq; setLinked(true);
    } catch (_) { setLinked(false); }
  }
  async function poll() {
    try {
      const s = await (await fetch(SYNC + 'state', { cache: 'no-store' })).json();
      setLinked(true);
      if (s.seq > lastSeq && s.total === STEPS.length) { lastSeq = s.seq; if (s.slide !== current) render(s.slide); }
    } catch (_) { setLinked(false); }
    setTimeout(poll, 700);
  }

  function fit() {
    const vw = window.innerWidth, vh = window.innerHeight;
    const s = Math.min((vw - 40) / 1000, (vh - 185) / 680);
    stage.style.setProperty('--s', s);
  }

  el('prev').onclick = prev;
  el('next').onclick = next;
  el('full').onclick = toggleFull;
  function toggleFull() {
    if (!document.fullscreenElement) (document.documentElement.requestFullscreen || (() => {})).call(document.documentElement);
    else (document.exitFullscreen || (() => {})).call(document);
  }
  document.addEventListener('keydown', (e) => {
    const k = e.key;
    if (k === 'ArrowRight' || k === ' ' || k === 'PageDown') { e.preventDefault(); next(); }
    else if (k === 'ArrowLeft' || k === 'PageUp') { e.preventDefault(); prev(); }
    else if (k.toLowerCase() === 'f') toggleFull();
  });
  // swipe — LEFT goes back, RIGHT goes forward
  let sx = 0, sy = 0, st = 0;
  el('app').addEventListener('touchstart', (e) => { const t = e.changedTouches[0]; sx = t.clientX; sy = t.clientY; st = Date.now(); }, { passive: true });
  el('app').addEventListener('touchend', (e) => {
    const t = e.changedTouches[0], dx = t.clientX - sx, dy = t.clientY - sy;
    if (Date.now() - st < 800 && Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy) * 1.3) { if (dx < 0) prev(); else next(); }
  }, { passive: true });
  window.addEventListener('resize', fit);

  async function init() {
    fit();
    try {
      const s = await (await fetch(SYNC + 'state', { cache: 'no-store' })).json();
      lastSeq = s.seq; render(s.total === STEPS.length ? s.slide : 0); setLinked(true);
    } catch (_) { render(0); setLinked(false); }
    poll();
  }
  init();
})();
