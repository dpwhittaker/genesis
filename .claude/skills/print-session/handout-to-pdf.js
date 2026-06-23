#!/usr/bin/env node
/*
 * handout-to-pdf.js — render a published genesis page to a print-accurate PDF.
 *
 * The genesis site has no local Jekyll build (no Ruby on this machine), so the
 * "real" renderer is the deployed GitHub Pages output. This script loads the
 * LIVE page with headless Chrome, emulates print media (so _includes/custom-head
 * print CSS and any <div class="page-break"> markers apply), and writes a
 * Letter-size PDF whose pagination matches what the class will actually print.
 *
 * Because it renders the live site, push your marker changes and let Pages
 * deploy BEFORE running this (see SKILL.md for the loop).
 *
 * Usage:
 *   node .claude/skills/print-session/handout-to-pdf.js <slug|site-path|url> [out.pdf]
 *
 * Examples:
 *   node .claude/skills/print-session/handout-to-pdf.js 01-the-neighbors-stories
 *   node .claude/skills/print-session/handout-to-pdf.js sessions/05-the-garden/
 *   node .claude/skills/print-session/handout-to-pdf.js https://dpwhittaker.github.io/genesis/sessions/08-babel/
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

function buildUrl(arg) {
  const base = (process.env.GENESIS_BASE_URL || 'https://dpwhittaker.github.io/genesis/').replace(/\/+$/, '/') ;
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
  const arg = process.argv[2];
  if (!arg) {
    console.error('Usage: node handout-to-pdf.js <slug|site-path|url> [out.pdf]');
    process.exit(1);
  }
  const url = buildUrl(arg);
  const outPath = process.argv[3] || path.join('pdf', `${slugify(arg)}.pdf`);
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
