#!/usr/bin/env node
/*
 * handout-to-pdf.js — render a genesis page to a print-accurate PDF.
 *
 * It loads the page with headless Chrome, emulates print media (so the
 * assets/main.scss @media print rules and any <div class="page-break"> markers
 * apply), and writes a Letter-size PDF whose pagination matches what the class
 * will actually print.
 *
 * TWO render targets:
 *   --local  → the local Jekyll preview (genesis-preview.service on :4000), which
 *              builds the WORKING TREE identically to GitHub Pages. Use this while
 *              tuning page breaks — no deploy, sub-second rebuilds. Start it with
 *              ./serve-local.sh (or `systemctl start genesis-preview`).
 *   default  → the deployed GitHub Pages site. Use this for a final check, and
 *              for the publish-lesson precondition (which verifies the LIVE page).
 *
 * Usage:
 *   node .claude/skills/print-session/handout-to-pdf.js [--local] <slug|site-path|url> [out.pdf]
 *
 * Examples:
 *   node .claude/skills/print-session/handout-to-pdf.js --local 02-history-or-poetry
 *   node .claude/skills/print-session/handout-to-pdf.js 01-the-neighbors-stories
 *   node .claude/skills/print-session/handout-to-pdf.js https://dpwhittaker.github.io/genesis/sessions/08-babel/
 *
 * Override the base explicitly with GENESIS_BASE_URL if needed.
 *
 * Output defaults to pdf/<slug>.pdf (the pdf/ dir is gitignored).
 *
 * Requires puppeteer. Resolution order: local node_modules, then $PUPPETEER_DIR,
 * then a sibling project's install. Install cleanly with:  npm i puppeteer
 */

const path = require('path');
const fs = require('fs');

function loadPuppeteer() {
  const tries = [
    () => require('puppeteer'),
    () => require(path.join(process.env.PUPPETEER_DIR || '', 'puppeteer')),
    // Fallback: reuse a sibling project's install if present (this machine has
    // one in ../systematic-theology). Relative, not an absolute personal path.
    () => require(path.resolve(__dirname, '../../../..', 'systematic-theology/node_modules/puppeteer')),
  ];
  for (const t of tries) {
    try { return t(); } catch (_) { /* keep trying */ }
  }
  console.error('puppeteer not found. Install it:  npm i puppeteer');
  console.error('or point at an existing install:  PUPPETEER_DIR=/path/to/node_modules node ...');
  process.exit(1);
}

function buildUrl(arg, useLocal) {
  const fallback = useLocal
    ? 'http://127.0.0.1:4000/genesis/'
    : 'https://dpwhittaker.github.io/genesis/';
  const base = (process.env.GENESIS_BASE_URL || fallback).replace(/\/+$/, '/') ;
  if (/^https?:\/\//.test(arg)) return arg;
  let p = arg.replace(/^\/+/, '');
  // bare slug like "01-the-neighbors-stories" -> sessions/<slug>/
  if (!p.includes('/')) p = `sessions/${p}/`;
  if (!/\.html?$/.test(p) && !p.endsWith('/')) p += '/';
  return base.endsWith('/') ? base + p : base + '/' + p;
}

function slugify(arg) {
  let s = arg.replace(/^https?:\/\/[^/]+\//, '').replace(/\.html?$/, '');
  s = s.replace(/\/+$/, '').split('/').filter(Boolean).pop() || 'page';
  return s;
}

async function main() {
  const rawArgs = process.argv.slice(2);
  const useLocal = rawArgs.includes('--local');
  const pos = rawArgs.filter((a) => a !== '--local');
  const arg = pos[0];
  if (!arg) {
    console.error('Usage: node handout-to-pdf.js [--local] <slug|site-path|url> [out.pdf]');
    process.exit(1);
  }
  const url = buildUrl(arg, useLocal);
  const outPath = pos[1] || path.join('pdf', `${slugify(arg)}.pdf`);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });

  const puppeteer = loadPuppeteer();
  console.log(`Rendering ${url}`);

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  try {
    const page = await browser.newPage();
    const resp = await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });
    if (!resp || !resp.ok()) {
      throw new Error(`page load failed: HTTP ${resp ? resp.status() : '??'} for ${url}`);
    }
    await page.emulateMediaType('print');
    await page.pdf({
      path: outPath,
      format: 'Letter',
      margin: { top: '0.5in', bottom: '0.5in', left: '0.5in', right: '0.5in' },
      printBackground: true,
    });
    console.log(`PDF written to ${outPath}`);
  } finally {
    await browser.close();
  }
}

main().catch((err) => { console.error(err.message || err); process.exit(1); });
