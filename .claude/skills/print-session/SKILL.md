---
name: print-session
description: Prepare a genesis session/handout page for printing — place page breaks at natural section boundaries and verify the layout by rendering the page to PDF and analyzing per-page density. Use when the user wants to print or hand out a session, asks to "fix the page breaks," "make it print cleanly," "get it ready for class," or after a session's content is finalized. Tuned to the Jekyll + minima + GitHub Pages pipeline: print CSS lives in assets/main.scss. A local Jekyll preview (genesis-preview.service on :4000) builds the working tree identically to Pages, so iterate with `--local` (no deploy) and do one live check at the end.
---

# Print a genesis session for handout

Genesis session pages (`sessions/<NN-slug>/index.md`) are markdown, served as HTML by Jekyll/minima on GitHub Pages, and **handed out to the class on paper**. This skill makes a finished session paginate well: sections don't straddle page boundaries, headings don't strand at a page foot, and the printout is an even number of pages for double-sided printing.

Adapted from the systematic-theology handout workflow, retuned for this pipeline. There is a **local Jekyll preview** — `genesis-preview.service` (or `./serve-local.sh`) serves the working tree at `http://127.0.0.1:4000/genesis/`, built identically to GitHub Pages (same minima theme, kramdown, `/genesis` baseurl, compiled `main.css`). Render that with `--local` and iterate page breaks in seconds — no commit, no deploy. Do a single live render at the end to confirm. Don't count source lines to guess page length — blockquotes, tables, and wrapping make it unreliable; render and measure.

## When to run

After a session's *content* is final. Page-break placement is a dedicated finishing pass, not something to fiddle with mid-draft.

## What's already in place

- **Print CSS** — `assets/main.scss` imports minima and appends an `@media print` block (Letter, 0.5in margins, black-on-white, site chrome hidden). It keeps headings with the text below them and prevents blockquotes/tables/list items from splitting across pages. You normally don't touch this. (It compiles to `/assets/main.css`, the stylesheet minima already links — minima's `custom-head.html` include is not wired up in this build, so the override goes through the stylesheet, not the head.)
- **Local preview server** — `genesis-preview.service` runs `./serve-local.sh` (Jekyll on `127.0.0.1:4000`, `--baseurl /genesis`), built from `Gemfile.local` into `vendor/bundle` (all gitignored / excluded from the published site). It is also wired as the project's claude-hub Open target via `.project-meta.json` (`proxyTarget`), so `/genesis/` on the landing page shows this live preview.
- **Tools** (in this skill dir):
  - `handout-to-pdf.js` — renders a page to `pdf/<slug>.pdf` (headless Chrome, print media emulated). `--local` targets the preview server; otherwise the deployed site.
  - `analyze-pdf.py` — reports per-page fullness, headroom in inches, char count, and first heading; flags sparse / overfull / **tight** pages and **orphaned discussion boxes**; checks even page count.

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

Iterate against the **local** server — each cycle is edit → render → analyze, no commit, no deploy:

```bash
# 0. once: make sure the local preview is running (autostarts on boot).
systemctl is-active genesis-preview.service || (./serve-local.sh &)

# loop: edit <div class="page-break"></div> markers in sessions/<NN-slug>/index.md,
#       then render the LOCAL build (working tree, no commit) and analyze.
#       --print-safe reserves the space Chrome's print dialog takes for its
#       header/footer; without it the page count reads low. Always use it.
node .claude/skills/print-session/handout-to-pdf.js --local --print-safe <NN-slug>
source ~/ml-env/bin/activate
python3 .claude/skills/print-session/analyze-pdf.py pdf/<NN-slug>.pdf
# repeat until no warnings + even page count.
```

The local server rebuilds the working tree on every save (sub-second) and is byte-identical to GitHub Pages (verified: same per-page fullness as the deployed render). When the layout is final, commit + push, let Pages deploy, and do **one** live confirmation:

```bash
git add sessions/<NN-slug>/index.md && git commit -m "..." && git push origin main
rid=$(gh run list --repo dpwhittaker/genesis --workflow pages-build-deployment -L 1 --json databaseId --jq '.[0].databaseId')
gh run watch "$rid" --repo dpwhittaker/genesis --exit-status
node .claude/skills/print-session/handout-to-pdf.js <NN-slug>   # live (no --local)
python3 .claude/skills/print-session/analyze-pdf.py pdf/<NN-slug>.pdf
```

Read the analyzer output:
- **`sparse` interior page (<25% full)** — the section before it overflowed by a little and dragged a sliver onto a near-empty page. Tighten that section (steps above) or move a `<div class="page-break">` earlier so the split lands cleanly.
- **`overfull` page (>97%)** — content may be clipping; add a break or trim.
- **`tight` page (under 0.6in headroom)** — renders fine *here* and still spills on a real printer. Treat it as a real failure, not a cosmetic one; trim that page until it clears 0.6in. See "Leave headroom" below.
- **`orphan` discussion box** — a `.discuss` box is the first thing on a page, meaning it got pushed off the section it belongs to. Trim the previous page or move the break.
- **odd total page count** — relax a break or expand a section to reach an even count.

Iterate until no warnings and the page count is even. Then the session is handout-ready.

## Leave headroom — the renderer is not the printer

A page can render perfectly here and still break on paper. Headless Chrome and a
person's print dialog do not have identical usable height: **"Headers and footers"
is on by default in Chrome's print dialog and reserves roughly 0.4in top and
bottom.** A page with less headroom than that will reflow when actually printed.

**Use `--print-safe` and this stops being guesswork.** It injects a later
`@page { margin: 0.95in 0.5in }` rule, reproducing the ~0.8in the print dialog
takes for its header and footer, so the render *is* the page the reader gets:

```bash
node .claude/skills/print-session/handout-to-pdf.js --local --print-safe <NN-slug>
```

The injection matters: `main.scss` declares `@page { margin: 0.5in }`, and **a CSS
`@page` margin beats puppeteer's `margin` option**, so passing margins to
`page.pdf()` silently does nothing. Override the rule, not the option.

Session 5 is the cautionary tale. The default render said 8 clean pages; the user
printed 12, with three pages holding a few lines and one blank. Reserving the
0.95in reproduced all 12 exactly — the analyzer had been measuring a page that
does not exist. Guess the ratio from a page-count report if you ever need to: for
exactly the pages at 92–93% to spill while a 90% page holds, usable height must be
~0.91× the optimistic render, which is the header/footer reserve.

Two consequences worth internalising:

- **Under `--print-safe`, the `tight` warning double-counts.** The reserve is
  already subtracted, so 0.55in of residual room is 0.55in of *real* slack. Don't
  trim prose chasing it. To check robustness properly, re-render at a larger
  reserve — `PRINT_SAFE_MARGIN=1.25in` — and confirm the page count holds.
- **In a flowing layout, `tight` mostly isn't a defect at all.** The gap at a page
  foot *is* the block that would not fit; Chrome has already broken safely. The
  warning earns its keep on pages packed against a forced break.

Density is not the same as safety — a page at 92% full with a 5% unsplittable box
at the bottom is one printer setting away from being a 9-page handout.

Worth telling the user once: unchecking "Headers and footers" in the print dialog
buys back that space. But the handout should not depend on it.

## Forced breaks are expensive — flow first

A `<div class="page-break">` before every `##` looks tidy in the markdown and
costs, on average, **half a page each**. Session 5 ran 14 pages with thirteen
breaks and **8 pages with one**, on essentially the same text — the section-per-page
rule, not the word count, was the page count.

So when a handout must hit a page budget: **delete the breaks, render, and see what
flow gives you** before cutting a single sentence. Then spend the leftover slack on
one or two breaks at the boundaries that matter most, re-rendering to confirm the
count holds. Sections starting mid-page is normal for a dense handout; that is what
the `h2 { page-break-after: avoid }` rule is there to make safe.

## Notes / gotchas

- **Puppeteer:** `handout-to-pdf.js` needs it. It auto-resolves a local install, then `$PUPPETEER_DIR`, then a sibling project's `node_modules`. Cleanest: `npm i puppeteer` once (the resulting `node_modules/` is gitignored).
- **pymupdf** lives in the ML venv — `source ~/ml-env/bin/activate` before the analyzer.
- **Generated PDFs** go to `pdf/` (gitignored) — they're build artifacts, not source.
- This skill targets a single session page. To prep several, run the `--local` loop per slug — no deploy between them.
- **Preview server down?** `sudo systemctl restart genesis-preview.service` (logs: `journalctl -u genesis-preview.service`). If `--local` renders fail to connect, that service isn't running.
