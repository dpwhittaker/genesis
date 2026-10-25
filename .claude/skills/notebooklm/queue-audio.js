// Queues a lesson's two Deep Dive episodes in an open Gemini Notebook (NotebookLM)
// notebook, one after the other: Audio Overview tile → Customize dialog → Deep Dive,
// English, the length preset, the focus prompt → "Generate now".
//
// Don't run this file directly: queue-audio-js.sh prepends `const CONFIG = {...}` (each
// episode's length preset and focus prompt, checked) and prints the whole script, which
// goes in ONE javascript_tool call on the notebook tab. It returns what it queued and
// what the Studio panel listed afterwards. With CONFIG.dryRun it fills and checks each
// dialog, then closes it instead of generating.

const sleep = ms => new Promise(r => setTimeout(r, ms));
const waitFor = async (fn, what, ms = 10000) => {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) { const v = fn(); if (v) return v; await sleep(200); }
  throw new Error('timed out waiting for ' + what);
};
const text = el => el ? el.textContent.replace(/\s+/g, ' ').trim() : '';
// The Studio tile is a div, not a button, and opens the Customize dialog directly.
const tile = () => document.querySelector('[aria-label="Audio Overview"].create-artifact-button-container');
// The page has other textareas (web search, chat) and a hidden emoji-palette dialog,
// so find the Customize dialog through its focus box.
const focusBox = () => document.querySelector('textarea[aria-label="What should the AI hosts focus on in this episode?"]');
const setValue = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;

const queued = [];
for (const { name, length, focus } of CONFIG.episodes) {
  if (!focusBox()) (await waitFor(tile, 'the Audio Overview tile')).click();
  const box = await waitFor(focusBox, 'the Customize dialog');
  const dlg = box.closest('mat-dialog-container');
  const button = label => [...dlg.querySelectorAll('button')].find(b => text(b) === label);

  // Format tiles are mat-radio-buttons around real radio inputs; Deep Dive is the first.
  const deep = [...dlg.querySelectorAll('mat-radio-button')].find(r => text(r).startsWith('Deep Dive'));
  if (!deep) throw new Error('no Deep Dive format tile');
  const deepInput = deep.querySelector('input[type=radio]');
  if (!deepInput.checked) deepInput.click();
  await waitFor(() => deepInput.checked, 'Deep Dive to be selected');

  const lang = text(dlg.querySelector('mat-select'));
  if (!lang.startsWith('English')) throw new Error(`the language is "${lang}", not English`);

  // Length is a toggle group: Short / Default / Long, each a button with role=radio.
  const len = [...dlg.querySelectorAll('button[role=radio]')].find(b => text(b) === length);
  if (!len) throw new Error(`no "${length}" length button`);
  if (len.getAttribute('aria-checked') !== 'true') len.click();
  await waitFor(() => len.getAttribute('aria-checked') === 'true', `"${length}" to be selected`);

  box.focus();
  setValue.call(box, focus);
  box.dispatchEvent(new Event('input', { bubbles: true }));
  box.dispatchEvent(new Event('change', { bubbles: true }));
  if (box.value !== focus) throw new Error('the focus box did not take the prompt');

  // "6 sources" on the source picker: all of the notebook's sources, unless someone unticked one.
  const sources = text([...dlg.querySelectorAll('button')].find(b => /^\d+ sources?/.test(text(b)))).replace(/keyboard_arrow_down$/, '');
  if (CONFIG.dryRun) {
    dlg.querySelector('button[aria-label="Close dialog"]').click();
  } else {
    // "Generate now", not "Generate later".
    (await waitFor(() => { const b = button('Generate now'); return b && !b.disabled && b; }, 'an enabled "Generate now"')).click();
  }
  await waitFor(() => !focusBox(), 'the dialog to close', 20000);
  await sleep(2000);
  queued.push({ name, length, sources, focusChars: focus.length, generated: !CONFIG.dryRun });
}
({ queued, studio: [...document.querySelectorAll('artifact-library-item')].map(text) })
