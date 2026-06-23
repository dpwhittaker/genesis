---
name: print-session
description: Prepare a genesis session/handout page for printing — place page breaks at natural section boundaries and verify the layout by rendering the live published page to PDF and analyzing per-page density. Use when the user wants to print or hand out a session, asks to "fix the page breaks," "make it print cleanly," "get it ready for class," or after a session's content is finalized. Tuned to the Jekyll + minima + GitHub Pages pipeline: print CSS lives in _includes/custom-head.html; the renderer is the deployed page, so push before verifying.
---

# Print a genesis session for handout

Genesis session pages (`sessions/<NN-slug>/index.md`) are markdown, served as HTML by Jekyll/minima on GitHub Pages, and **handed out to the class on paper**. This skill makes a finished session paginate well: sections don't straddle page boundaries, headings don't strand at a page foot, and the printout is an even number of pages for double-sided printing.

Adapted from the systematic-theology handout workflow, retuned for this pipeline. The big difference: there is **no local Jekyll build** here (no Ruby), so the print-accurate renderer is the **live published page**. Push your changes, let Pages deploy, then render the live URL to PDF. Don't count source lines to guess page length — blockquotes, tables, and wrapping make it unreliable; render and measure.

## When to run

After a session's *content* is final. Page-break placement is a dedicated finishing pass, not something to fiddle with mid-draft.

## What's already in place

- **Print CSS** — `_includes/custom-head.html` injects an `@media print` block (Letter, 0.5in margins, black-on-white, site chrome hidden). It keeps headings with the text below them and prevents blockquotes/tables/list items from splitting across pages. You normally don't touch this.
- **Tools** (in this skill dir):
  - `handout-to-pdf.js` — renders a live page to `pdf/<slug>.pdf` (headless Chrome, print media emulated).
  - `analyze-pdf.py` — reports per-page fullness, char count, and first heading; flags sparse/overfull pages; checks even page count.

## Markers you place in the markdown

- **Forced page break:** put `<div class="page-break"></div>` on its own line where the next content must start a new printed page. Invisible on screen, a hard break in print. This is the one knob you place by hand during the page-break pass.
- **Section divider (no break):** a plain `---` rule. Renders as a divider on screen and in print but does **not** force a new page. (Sessions already use these.)
- **Hide from print:** mark on-screen-only bits (e.g. the "← Back to all sessions" link) with kramdown's inline attribute so they vanish on paper:
  ```markdown
  [← Back to all sessions](../../)
  {: .no-print}
  ```

## Page-break philosophy

`#` (h1) is the page title; content sections begin at `##` (h2).

1. **No `h2` section should span more than one page** unless it genuinely cannot fit on one. Aim for one section, one self-contained block of pages.
2. **Maximize content per page.** Don't scatter forced breaks; let the print CSS keep headings and atomic blocks intact, and add a `<div class="page-break">` only where a section would otherwise start near a page foot and spill awkwardly.
3. **Minimize mid-section page turns.** A reader should be able to follow one `##` section without flipping the page. When a section must span two pages, put the break at a natural pause — between sub-points, after a conclusion, before a new excerpt — never mid-thought.
4. **Aim for an even total page count** (handouts print double-sided; an odd count wastes a blank back page). There's little difference between 5 and 6 pages — prefer relaxing a break or letting a section breathe over cutting good content, unless cutting is the better editorial call.

## When a section overruns its page, fix it in this order

Before adding a new page break, try to make the section *fit*:

1. **Reword short-ending paragraphs.** If a paragraph's last line holds ≤5 words, tighten the paragraph to reclaim a line — same meaning, fewer lines.
2. **Trim low-value detail.** Cut asides, qualifications, and elaborations that don't carry the session's point. Protect the core claims and the primary-source excerpts.
3. **Ellipsize a long quote (last resort).** Shorten a Scripture or ANE quotation by ellipsizing the least-relevant span — never in a way that changes its meaning.

If none of these land the layout, describe the stubborn section to the user and ask before cutting further.

## The verification loop

Because rendering is live, each iteration is: edit → push → wait for deploy → render → analyze.

```bash
# 1. place/adjust <div class="page-break"></div> markers in
#    sessions/<NN-slug>/index.md, then commit + push:
git add sessions/<NN-slug>/index.md && git commit -m "..." && git push origin main

# 2. wait for the Pages build to finish (it must deploy before you render):
rid=$(gh run list --repo dpwhittaker/genesis --workflow pages-build-deployment -L 1 --json databaseId --jq '.[0].databaseId')
gh run watch "$rid" --repo dpwhittaker/genesis --exit-status

# 3. render the live page to PDF:
node .claude/skills/print-session/handout-to-pdf.js <NN-slug>

# 4. analyze page density:
source ~/ml-env/bin/activate
python3 .claude/skills/print-session/analyze-pdf.py pdf/<NN-slug>.pdf
```

Read the analyzer output:
- **`sparse` interior page (<25% full)** — the section before it overflowed by a little and dragged a sliver onto a near-empty page. Tighten that section (steps above) or move a `<div class="page-break">` earlier so the split lands cleanly.
- **`overfull` page (>97%)** — content may be clipping; add a break or trim.
- **odd total page count** — relax a break or expand a section to reach an even count.

Iterate until no warnings and the page count is even. Then the session is handout-ready.

## Notes / gotchas

- **Puppeteer:** `handout-to-pdf.js` needs it. It auto-resolves a local install, then `$PUPPETEER_DIR`, then a sibling project's `node_modules`. Cleanest: `npm i puppeteer` once (the resulting `node_modules/` is gitignored).
- **pymupdf** lives in the ML venv — `source ~/ml-env/bin/activate` before the analyzer.
- **Generated PDFs** go to `pdf/` (gitignored) — they're build artifacts, not source.
- This skill targets a single session page. To prep several, run the loop per slug (batch the renders after one deploy).
