// Reports the Audio Overviews in an open Gemini Notebook (NotebookLM) notebook and,
// once CONFIG.expect of them are finished, downloads each through More → Download.
// Chrome saves them to its downloads folder (~/Downloads for the Chrome on this host),
// named after each episode's title.
//
// Paste the whole file as `text` in ONE javascript_tool call on the notebook tab. Until
// every episode is ready it only reports, so it serves as the check after each wait; it
// never downloads a partial set. Once it has downloaded, don't run it again on the same
// notebook: it would download the episodes a second time.
const CONFIG = { expect: 2 };

const sleep = ms => new Promise(r => setTimeout(r, ms));
const waitFor = async (fn, what, ms = 10000) => {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) { const v = fn(); if (v) return v; await sleep(200); }
  throw new Error('timed out waiting for ' + what);
};
const text = el => el ? el.textContent.replace(/\s+/g, ' ').trim() : '';
const seconds = d => d.split(':').reduce((s, n) => s * 60 + Number(n), 0);
const menuItems = () => [...document.querySelectorAll('[role=menuitem]')].filter(m => m.offsetParent);

// Each Studio output is an <artifact-library-item>. A finished episode has the
// audio_spark icon and details that start with its duration:
// "48:37 · Deep Dive · 6 sources · 1d ago".
const items = [...document.querySelectorAll('artifact-library-item')].map(el => {
  const details = text(el.querySelector('.artifact-details'));
  const m = details.match(/^(\d+(?::\d{2}){1,2})\b/);
  const ready = text(el.querySelector('.artifact-icon')) === 'audio_spark' && !!m;
  return { el, ready, title: text(el.querySelector('.artifact-title')), duration: m && m[1], details: ready ? details : text(el) };
});
const ready = items.filter(i => i.ready);
const studio = items.map(({ title, ready, details }) => ({ title, ready, details }));

let result;
if (ready.length < CONFIG.expect) {
  result = { waiting: `${ready.length} of ${CONFIG.expect} ready`, studio };
} else if (ready.length > CONFIG.expect) {
  throw new Error(`${ready.length} finished episodes, expected ${CONFIG.expect}; download the right ones by hand`);
} else {
  // Longest first, so with the usual pair the first is the long episode.
  ready.sort((a, b) => seconds(b.duration) - seconds(a.duration));
  const downloaded = [];
  for (const i of ready) {
    i.el.querySelector('.artifact-actions button[aria-label="More"]').click();
    (await waitFor(() => menuItems().find(m => text(m).endsWith('Download')), 'the Download menu item')).click();
    await sleep(1500);
    if (menuItems().length) document.querySelector('.cdk-overlay-backdrop')?.click();
    await waitFor(() => !menuItems().length, 'the menu to close');
    downloaded.push({ title: i.title, duration: i.duration });
  }
  result = { downloaded };
}
result
