// Adds a lesson's sources to an open Gemini Notebook (NotebookLM) notebook as
// "Copied text", fetching each file from the public repo instead of retyping it.
//
// Don't run this file directly: add-sources-js.sh prepends `const CONFIG = {...}`
// (the pinned commit, the paths, the expected byte size of each cleaned file) and
// prints the whole script, which goes in ONE javascript_tool call on the notebook
// tab. It returns [{path, bytes}] for every source it inserted.
//
// raw.githubusercontent.com answers with Access-Control-Allow-Origin: *, so the
// notebook page can fetch from it. The commit is pinned by SHA, so what gets pasted
// is exactly what was committed and pushed.

// Same cleaning as clean() in prep-sources.sh: drop the front matter, HTML tags and
// kramdown {: …} lines, keep link text, decode a few entities, squeeze blank runs.
// KEEP THE TWO IN STEP: the byte-size check below compares against prep-sources.sh.
const clean = (md) => {
  let lines = md.split('\n');
  if (lines[lines.length - 1] === '') lines.pop();          // trailing newline ends the last line
  if (lines[0] === '---') {
    const end = lines.indexOf('---', 1);
    if (end > 0) lines = lines.slice(end + 1);
  }
  const out = [];
  for (const raw of lines) {
    const l = raw
      .replace(/<[^>]+>/g, '')
      .replace(/^\{:.*\}$/, '')
      .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
      .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&mdash;/g, '—')
      .replace(/&ldquo;/g, '"').replace(/&rdquo;/g, '"');
    if (l === '' && out.length && out[out.length - 1] === '') continue;   // cat -s
    out.push(l);
  }
  return out.map(l => l + '\n').join('');
};

const sleep = ms => new Promise(r => setTimeout(r, ms));
const waitFor = async (fn, what, ms = 10000) => {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) { const v = fn(); if (v) return v; await sleep(200); }
  throw new Error('timed out waiting for ' + what);
};
// Material buttons carry their icon's ligature in textContent ("add Add sources"),
// so match the end of the text, and only visible buttons.
const button = (label) => [...document.querySelectorAll('button')]
  .find(b => b.offsetParent !== null && b.textContent.replace(/\s+/g, ' ').trim().endsWith(label));
// The page has three textareas: the web-search "Discover sources" box, the chat
// "Query box", and, in the Copied text form, this one. Target it by its label.
const pasteBox = () => document.querySelector('textarea[aria-label="Pasted text"]');
const setValue = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;

const added = [];
for (const { path, bytes } of CONFIG.files) {
  const r = await fetch(CONFIG.base + path);
  if (!r.ok) throw new Error(`fetch ${path}: HTTP ${r.status}`);
  const text = clean(await r.text());
  const got = new TextEncoder().encode(text).length;
  if (got !== bytes) throw new Error(`${path}: cleaned to ${got} bytes, prep-sources.sh made ${bytes}`);

  // A new notebook may open the add-source dialog by itself; otherwise open it.
  if (!button('Copied text')) (await waitFor(() => button('Add sources'), '"Add sources"')).click();
  (await waitFor(() => button('Copied text'), '"Copied text"')).click();
  const box = await waitFor(pasteBox, 'the "Pasted text" box');
  box.focus();
  setValue.call(box, text);
  box.dispatchEvent(new Event('input', { bubbles: true }));
  box.dispatchEvent(new Event('change', { bubbles: true }));
  const insert = await waitFor(() => { const b = button('Insert'); return b && !b.disabled && b; }, 'an enabled "Insert"');
  insert.click();
  await waitFor(() => !pasteBox(), 'the dialog to close', 20000);
  await sleep(1500);
  added.push({ path, bytes });
}
added
