/* The Neighbors' Stories — slideshow engine.
 *
 * Art-agnostic and sync-ready by design:
 *   - Scenes register themselves (window.SLIDESHOW.registerScene). A scene is data:
 *     SVG art string, optional scene CSS, a list of labelled entities, and named
 *     animations. Today entities are inline SVG <g> and animations are JS
 *     timelines; the runner also accepts {type:'video', href} so an SDXL/WAN clip
 *     can replace a CSS timeline with no engine change.
 *   - Every interaction flows through dispatch(action) -> apply(action). Sync.send
 *     is the one no-op seam where phone->TV WebSocket mirroring will plug in;
 *     remote actions will call apply() directly (no echo).
 */
(function () {
  'use strict';
  const SCENES = [];
  const el = (id) => document.getElementById(id);
  const NS = 'http://www.w3.org/2000/svg';
  const FULL = [0, 0, 1920, 1080];

  let camera, overlay, panel, stageEl, hintTimer;
  const state = { i: 0, active: null, mode: 'overview', busy: false };

  /* ---------- sync seam (phase 2) ---------- */
  const Sync = {
    send() {},                 // -> ws.send(JSON.stringify(action)) later
    onRemote(/* cb */) {},     // -> ws.onmessage applies remote actions
  };

  function dispatch(action) { apply(action); Sync.send(action); }

  function apply(action) {
    switch (action.type) {
      case 'goto':     gotoScene(action.index); break;
      case 'next':     gotoScene(state.i + 1); break;
      case 'prev':     gotoScene(state.i - 1); break;
      case 'activate': activate(action.entityId); break;
      case 'reset':    resetView(); break;
    }
  }

  /* ---------- camera (viewBox tween) ---------- */
  let camRAF = null;
  function tweenViewBox(target, ms) {
    const from = camera.getAttribute('viewBox').split(/\s+/).map(Number);
    if (camRAF) cancelAnimationFrame(camRAF);
    if (!ms) { camera.setAttribute('viewBox', target.join(' ')); return Promise.resolve(); }
    const t0 = performance.now();
    const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
    return new Promise((res) => {
      (function step(now) {
        const t = Math.min(1, (now - t0) / ms), e = ease(t);
        camera.setAttribute('viewBox', from.map((f, k) => f + (target[k] - f) * e).join(' '));
        if (t < 1) camRAF = requestAnimationFrame(step); else res();
      })(t0);
    });
  }

  /* ---------- scene lifecycle ---------- */
  const scene = () => SCENES[state.i];

  function gotoScene(i) {
    if (i < 0 || i >= SCENES.length || i === state.i && camera.innerHTML) { if (i !== state.i) return; }
    if (i < 0 || i >= SCENES.length) return;
    state.i = i; state.active = null; state.mode = 'overview'; state.busy = false;
    const sc = scene();
    camera.setAttribute('viewBox', FULL.join(' '));
    camera.innerHTML = sc.svg;
    el('scene-style').textContent = sc.css || '';
    renderLabels(sc);
    hidePanel();
    overlay.classList.remove('dim');
    el('scene-title').textContent = sc.title;
    el('scene-source').textContent = sc.source;
    renderDots();
    setHint(sc.hint || 'Tap a label to explore — tap the glowing one to watch it happen.');
    if (sc.onEnter) sc.onEnter(makeApi());
  }

  function renderLabels(sc) {
    overlay.innerHTML = '';
    sc.entities.forEach((ent) => {
      const g = document.createElementNS(NS, 'g');
      g.setAttribute('class', 'label' + (ent.action ? ' is-action' : ''));
      g.dataset.entity = ent.id;
      const [px, py] = ent.point || ent.labelXY;
      const [lx, ly] = ent.labelXY;
      const tick = mk('line', { class: 'tick', x1: px, y1: py, x2: lx, y2: ly });
      const dot = mk('circle', { class: 'dot', cx: px, cy: py, r: 7 });
      const pill = mk('rect', { class: 'pill', rx: 26 });
      const text = mk('text', { class: 'pill-text', x: lx, y: ly, 'font-size': ent.labelSize || 30 });
      text.textContent = ent.label;
      g.append(tick, dot, pill, text);
      overlay.appendChild(g);
      const bb = text.getBBox(), padX = 28, padY = 15;
      attr(pill, { x: bb.x - padX, y: bb.y - padY, width: bb.width + padX * 2, height: bb.height + padY * 2 });
      g.addEventListener('click', (e) => { e.stopPropagation(); dispatch({ type: 'activate', entityId: ent.id }); });
    });
  }

  function activate(id) {
    if (state.busy) return;
    const sc = scene(), ent = sc.entities.find((e) => e.id === id);
    if (!ent) return;
    state.active = id;
    if (ent.action) runAnimation(sc, ent.action, ent);
    else magnify(ent);
  }

  function magnify(ent) {
    state.mode = 'magnify';
    overlay.classList.add('dim');
    setHint('');
    camera.classList.add('has-focus');
    const node = ent.svgId && camera.querySelector('#' + ent.svgId);
    if (node) node.classList.add('lit');
    tweenViewBox(ent.focus || FULL, 700).then(() => showPanel(ent));
  }

  function runAnimation(sc, name, ent) {
    const anim = sc.animations && sc.animations[name];
    if (!anim) return magnify(ent);
    state.busy = true; state.mode = 'animating';
    overlay.classList.add('dim'); hidePanel(); setHint('');
    const finish = () => { state.busy = false; showPanel(ent); };
    if (typeof anim === 'function') Promise.resolve(anim(makeApi())).then(finish);
    else if (anim.type === 'video') playVideo(anim.href).then(finish);   // future WAN clip
    else finish();
  }

  /* future-proofing: a generated clip can stand in for a CSS timeline */
  function playVideo(href) {
    return new Promise((res) => {
      const v = document.createElement('video');
      Object.assign(v, { src: href, autoplay: true, playsInline: true });
      v.className = 'scene-video';
      v.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:3';
      stageEl.appendChild(v);
      const done = () => { v.remove(); res(); };
      v.onended = done; v.onerror = done;
      // the hoe tap is a user gesture, so play with sound; fall back to muted if blocked
      v.play().catch(() => { v.muted = true; v.play().catch(done); });
    });
  }

  function showPanel(ent) {
    el('panel-title').innerHTML = ent.panelTitle || ent.label;
    el('panel-body').innerHTML = ent.text || '';
    panel.hidden = false;
  }
  function hidePanel() { panel.hidden = true; }

  function resetView() {
    const sc = scene();
    state.active = null; state.mode = 'overview'; state.busy = false;
    hidePanel(); overlay.classList.remove('dim');
    camera.classList.remove('has-focus');
    camera.querySelectorAll('.lit').forEach((n) => n.classList.remove('lit'));
    (sc.resetClasses || []).forEach((c) => stageEl.classList.remove(c));
    tweenViewBox(FULL, 600);
    setHint(sc.hint || '');
  }

  /* ---------- api handed to scene animations ---------- */
  function makeApi() {
    return {
      svg: camera,
      q: (sel) => camera.querySelector(sel),
      stage: stageEl,
      add: (c) => stageEl.classList.add(c),
      remove: (c) => stageEl.classList.remove(c),
      tween: tweenViewBox,
      FULL,
      wait: (ms) => new Promise((r) => setTimeout(r, ms)),
    };
  }

  /* ---------- chrome ---------- */
  function renderDots() {
    const d = el('scene-dots'); d.innerHTML = '';
    SCENES.forEach((_, k) => { const s = document.createElement('span'); s.className = 'd' + (k === state.i ? ' on' : ''); d.appendChild(s); });
  }
  function setHint(txt) {
    const h = el('hint'); h.textContent = txt || '';
    clearTimeout(hintTimer); h.classList.toggle('gone', !txt);
    if (txt) hintTimer = setTimeout(() => h.classList.add('gone'), 5000);
  }
  function toggleFull() {
    if (!document.fullscreenElement) { (document.documentElement.requestFullscreen || (() => {})).call(document.documentElement); document.body.classList.add('immersive'); }
    else { (document.exitFullscreen || (() => {})).call(document); document.body.classList.remove('immersive'); }
  }

  /* ---------- helpers ---------- */
  function mk(tag, attrs) { const n = document.createElementNS(NS, tag); attr(n, attrs); return n; }
  function attr(n, attrs) { for (const k in attrs) n.setAttribute(k, attrs[k]); return n; }

  function init() {
    camera = el('camera'); overlay = el('overlay'); panel = el('panel'); stageEl = el('stage');
    const style = document.createElement('style'); style.id = 'scene-style'; document.head.appendChild(style);
    el('btn-prev').onclick = () => dispatch({ type: 'prev' });
    el('btn-next').onclick = () => dispatch({ type: 'next' });
    el('btn-reset').onclick = () => dispatch({ type: 'reset' });
    el('btn-full').onclick = toggleFull;
    el('panel-close').onclick = () => dispatch({ type: 'reset' });
    stageEl.addEventListener('click', () => { if (state.mode !== 'overview' && !state.busy) dispatch({ type: 'reset' }); });
    document.addEventListener('keydown', (e) => {
      const k = e.key;
      if (k === 'ArrowRight') dispatch({ type: 'next' });
      else if (k === 'ArrowLeft') dispatch({ type: 'prev' });
      else if (k === 'Escape') dispatch({ type: 'reset' });
      else if (k.toLowerCase() === 'f') toggleFull();
    });
    Sync.onRemote(apply);
    gotoScene(0);
  }

  window.SLIDESHOW = {
    registerScene: (s) => SCENES.push(s),
    init,
    _dispatch: dispatch, _apply: apply, _state: state, _Sync: Sync,  // exposed for the phone-sync layer
  };
})();
