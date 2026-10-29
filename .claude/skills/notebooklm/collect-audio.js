// Reports the Audio Overviews in an open Gemini Notebook (NotebookLM) notebook: which
// are still generating, and, once CONFIG.expect of them are finished, each finished
// episode's title and duration, longest first.
//
// It does not download. "More → Download" opens a new tab that fetches the file, and
// Chrome blocks that tab unless the click is a real user gesture: a scripted .click()
// on the menu item silently does nothing (seen on Session 12, 2026-10-29). So download
// with real clicks, as SKILL.md step 7 says.
//
// Paste the whole file as `text` in ONE javascript_tool call on the notebook tab. It is
// safe to run as often as you like, so it serves as the check after each wait.
const CONFIG = { expect: 2 };

const text = el => el ? el.textContent.replace(/\s+/g, ' ').trim() : '';
const seconds = d => d.split(':').reduce((s, n) => s * 60 + Number(n), 0);

// Each Studio output is an <artifact-library-item>. A finished episode has the
// audio_spark icon and details that start with its duration:
// "48:37 · Deep Dive · 6 sources · 1d ago".
const items = [...document.querySelectorAll('artifact-library-item')].map(el => {
  const details = text(el.querySelector('.artifact-details'));
  const m = details.match(/^(\d+(?::\d{2}){1,2})\b/);
  const ready = text(el.querySelector('.artifact-icon')) === 'audio_spark' && !!m;
  return { ready, title: text(el.querySelector('.artifact-title')), duration: m && m[1], details: ready ? details : text(el) };
});
const ready = items.filter(i => i.ready);

let result;
if (ready.length < CONFIG.expect) {
  result = { waiting: `${ready.length} of ${CONFIG.expect} ready`, studio: items.map(({ title, ready, details }) => ({ title, ready, details })) };
} else if (ready.length > CONFIG.expect) {
  throw new Error(`${ready.length} finished episodes, expected ${CONFIG.expect}: pick the right ones by hand`);
} else {
  // Longest first, so with the usual pair the first is the long episode.
  ready.sort((a, b) => seconds(b.duration) - seconds(a.duration));
  result = { ready: ready.map(({ title, duration }) => ({ title, duration })) };
}
result
