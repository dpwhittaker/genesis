---
name: print-session
description: Prepare a genesis session/handout page for printing — place page breaks at natural section boundaries, render the handout to a PDF saved IN the session folder (sessions/<slug>/<slug>.pdf, linked from the page in a no-print line), and verify that exact file by analyzing per-page density. The class prints the PDF, not the web page, so what is checked is what is printed. Use when the user wants to print or hand out a session, asks to "fix the page breaks," "make it print cleanly," "get it ready for class," or after a session's content is finalized. Tuned to the Jekyll + minima + GitHub Pages pipeline: print CSS lives in assets/main.scss. A local Jekyll preview (genesis-preview.service on :4000) builds the working tree identically to Pages, so iterate with `--local` (no deploy).
---

# Print a genesis session for handout

Genesis session pages (`sessions/<NN-slug>/index.md`) are markdown, served as HTML by Jekyll/minima on GitHub Pages, and **handed out to the class on paper**. This skill makes a finished session paginate well — sections don't straddle page boundaries, headings don't strand at a page foot, the page count is even for double-sided printing — and **delivers the result as a PDF in the project**, which is what gets printed.

## The deliverable is a PDF in the session folder

**Print the PDF, never the web page.** Printing the page from a browser re-lays it out on the printer's terms: the print dialog's "Headers and footers" (on by default) eats ~0.4in top and bottom, a different browser or paper setting shifts every break, and a page that measured clean here comes out with a stranded line or an extra sheet. Every past print failure (Session 5: "8 clean pages" printed as 12) was that gap between the checked render and the printed one.

A PDF cannot reflow. So the pass ends by writing the handout to

```
sessions/<NN-slug>/<NN-slug>.pdf
```

— committed, served by Pages next to the handout — and **the file the analyzer checks is the file the user prints.** Consequences:

- **No reserve for the print dialog.** Publish renders use the plain 0.5in margins from `main.scss`. (`--print-safe` exists only for the case where someone insists on printing the web page; see the end of this file.)
- **`tight` and `overfull` stop being warnings.** Run the analyzer with `--direct` and they become informational notes. A full page is just full; headroom cannot be eaten by anything downstream. The real checks left are the ones about *layout*: sparse pages, orphaned discussion boxes, an odd page count — and, by eye, where the page turns fall.
- **Printing scale doesn't matter.** A viewer's "fit to page" shrinks the whole page uniformly; nothing moves between pages.
- **Links inside the PDF point at the live site.** `--publish` rewrites every link from the local preview to `https://dpwhittaker.github.io/genesis/` before rendering, so a reader who opens the PDF on a screen can still click through to the source sheets.

Link the PDF from the handout in a **no-print** line, directly under the `**Source sheets:**` line, so readers find it and it never appears on paper:

```markdown
🖨️ **[Printable handout (PDF)](<NN-slug>.pdf)** — print this file rather than the web page; it is the exact layout checked for paper.
{: .no-print}
```

**The PDF is a build artifact of `index.md`.** Any content change to the handout — a panel revision, a typo fix — means re-rendering the PDF (and re-checking it) before it's committed. A stale PDF is worse than none: it is the version people will actually hold.

## When to run

After a session's *content* is final, and again after any later content change (the PDF must match the page). Page-break placement is a dedicated finishing pass, not something to fiddle with mid-draft.

## What's already in place

- **Print CSS** — `assets/main.scss` imports minima and appends an `@media print` block (Letter, 0.5in margins, black-on-white, site chrome hidden). It keeps headings with the text below them and prevents blockquotes/tables/list items from splitting across pages. You normally don't touch this. (It compiles to `/assets/main.css`, the stylesheet minima already links — minima's `custom-head.html` include is not wired up in this build, so the override goes through the stylesheet, not the head.)
- **Local preview server** — `genesis-preview.service` runs `./serve-local.sh` (Jekyll on `127.0.0.1:4000`, `--baseurl /genesis`), built from `Gemfile.local` into `vendor/bundle` (all gitignored / excluded from the published site). It is also wired as the project's claude-hub Open target via `.project-meta.json` (`proxyTarget`), so `/genesis/` on the landing page shows this live preview.
- **Tools** (in this skill dir):
  - `handout-to-pdf.js` — renders a page with headless Chrome, print media emulated. `--local` targets the preview server (the working tree); `--publish` writes `sessions/<slug>/<slug>.pdf` with live-site links. Without `--publish`, output goes to `pdf/<slug>.pdf` (gitignored scratch).
  - `analyze-pdf.py` — reports per-page fullness, headroom in inches, char count, and first heading; flags sparse pages and **orphaned discussion boxes**; checks even page count. `--direct` marks the file as the one that prints (tight/overfull become notes).

## Markers you place in the markdown

- **Forced page break:** put `<div class="page-break"></div>` on its own line where the next content must start a new printed page. Invisible on screen, a hard break in print. This is the one knob you place by hand during the page-break pass.
- **Section divider (no break):** a plain `---` rule. Renders as a divider on screen and in print but does **not** force a new page. (Sessions already use these.)
- **Hide from print:** mark on-screen-only bits (e.g. the "← Back to all sessions" link, the PDF link, the 🎧 Listen block) with kramdown's inline attribute so they vanish on paper:
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
5. **Read the page turns, not just the numbers.** After each render, list the first and last line of every page (snippet below). A single word or line stranded at the top of a page ("widow"), or a heading with one line under it at a page foot, is a defect the density numbers don't show.

## When a section overruns its page, fix it in this order

Before adding a new page break, try to make the section *fit*:

1. **Reword short-ending paragraphs.** If a paragraph's last line holds ≤5 words, tighten the paragraph to reclaim a line — same meaning, fewer lines. The same move fixes a widow at the top of the next page: take ~10 characters out of that paragraph and the stray line comes home.
2. **Trim low-value detail.** Cut asides, qualifications, and elaborations that don't carry the session's point. Protect the core claims and the primary-source excerpts.
3. **Ellipsize a long quote (last resort).** Shorten a Scripture or ANE quotation by ellipsizing the least-relevant span — never in a way that changes its meaning.

If none of these land the layout, describe the stubborn section to the user and ask before cutting further.

## The verification loop

Iterate against the **local** server — each cycle is edit → render → analyze, no commit, no deploy. Render straight to the deliverable; there is no separate "check" render:

```bash
# 0. once: make sure the local preview is running (autostarts on boot).
systemctl is-active genesis-preview.service || (./serve-local.sh &)

# loop: edit <div class="page-break"></div> markers / tighten prose in
#       sessions/<NN-slug>/index.md, then render the working tree to the
#       published PDF and analyze THAT file.
node .claude/skills/print-session/handout-to-pdf.js --local --publish <NN-slug>
source ~/ml-env/bin/activate
python3 .claude/skills/print-session/analyze-pdf.py --direct sessions/<NN-slug>/<NN-slug>.pdf

# and look at where the pages turn:
python3 - <<'PY'
import pymupdf
d = pymupdf.open("sessions/<NN-slug>/<NN-slug>.pdf")
for i, p in enumerate(d, 1):
    lines = [l for l in p.get_text().splitlines() if l.strip()]
    print(f"p{i} FIRST: {lines[0][:70]}\n    LAST:  {lines[-1][:90]}")
PY
# repeat until no warnings, an even page count, and clean page turns.
```

Then **look at two or three pages as images** (`page.get_pixmap(dpi=70).save(...)`, then read the PNG) — tables, Hebrew, blockquotes and discussion boxes are where rendering surprises live.

The local server rebuilds the working tree on every save (sub-second) and is byte-identical to GitHub Pages, so the PDF rendered from it is the same one Pages would produce. When the layout is final, commit the handout **and its PDF together**, push, and confirm the PDF is served:

```bash
git add sessions/<NN-slug>/index.md sessions/<NN-slug>/<NN-slug>.pdf && git commit -m "..." && git push origin main
rid=$(gh run list --repo dpwhittaker/genesis --workflow pages-build-deployment -L 1 --json databaseId --jq '.[0].databaseId')
gh run watch "$rid" --repo dpwhittaker/genesis --exit-status
curl -sI https://dpwhittaker.github.io/genesis/sessions/<NN-slug>/<NN-slug>.pdf | head -1   # 200
```

Tell the user where to print from: the 🖨️ link on the page, or the file itself in the project (`sessions/<NN-slug>/<NN-slug>.pdf`, browsable through claude-hub's file viewer).

Read the analyzer output:
- **`sparse` interior page (<25% full)** — the section before it overflowed by a little and dragged a sliver onto a near-empty page. Tighten that section (steps above) or move a `<div class="page-break">` earlier so the split lands cleanly.
- **`orphan` discussion box** — a `.discuss` box is the first thing on a page, meaning it got pushed off the section it belongs to. Trim the section above it by the box's height (~3–5 lines) or move the break.
- **odd total page count** — relax a break or expand a section to reach an even count.
- **`tight` / full page** — under `--direct`, informational only. Don't trim prose chasing it.

## Forced breaks are expensive — flow first

A `<div class="page-break">` before every `##` looks tidy in the markdown and
costs, on average, **half a page each**. Session 5 ran 14 pages with thirteen
breaks and **8 pages with one**, on essentially the same text — the section-per-page
rule, not the word count, was the page count. Session 8 measured 10–11 pages with
four breaks and **8 with none**, once the PDF path removed the print-dialog reserve.

So when a handout must hit a page budget: **delete the breaks, render, and see what
flow gives you** before cutting a single sentence. Then spend the leftover slack on
one or two breaks at the boundaries that matter most, re-rendering to confirm the
count holds. Sections starting mid-page is normal for a dense handout; that is what
the `h2 { page-break-after: avoid }` rule is there to make safe. A page budget the
user gives ("aim for 10") was usually set against the old, reserve-eaten measurement;
if flow lands cleanly on fewer even pages, report that rather than padding with breaks.

## If someone prints the web page anyway — `--print-safe`

The PDF makes this section history, but it explains the failures the PDF avoids and
is the fallback if a page must be browser-printed.

Headless Chrome and a person's print dialog do not have identical usable height:
**"Headers and footers" is on by default in Chrome's print dialog and reserves
roughly 0.4in top and bottom.** `--print-safe` injects a later
`@page { margin: 0.95in 0.5in }` rule reproducing that reserve, so a scratch render
approximates the page a browser print produces:

```bash
node .claude/skills/print-session/handout-to-pdf.js --local --print-safe <NN-slug>   # -> pdf/<slug>.pdf
python3 .claude/skills/print-session/analyze-pdf.py pdf/<NN-slug>.pdf              # tight/overfull are real here
```

The injection matters: `main.scss` declares `@page { margin: 0.5in }`, and **a CSS
`@page` margin beats puppeteer's `margin` option**, so passing margins to
`page.pdf()` silently does nothing. Override the rule, not the option. Under
`--print-safe` the `tight` warning double-counts (the reserve is already
subtracted); check robustness with `PRINT_SAFE_MARGIN=1.25in` instead of trimming
prose. `--print-safe` and `--publish` are mutually exclusive.

## Notes / gotchas

- **Puppeteer:** `handout-to-pdf.js` needs it. It auto-resolves a local install, then `$PUPPETEER_DIR`, then a sibling project's `node_modules`. Cleanest: `npm i puppeteer` once (the resulting `node_modules/` is gitignored).
- **"Could not find Chrome (ver. …)":** the borrowed puppeteer pins a Chrome build that isn't in `~/.cache/puppeteer`. The script falls back to the system Chrome (`/usr/bin/google-chrome`) automatically; `PUPPETEER_EXECUTABLE_PATH=/usr/bin/google-chrome` forces it. Renders are identical for our purposes.
- **pymupdf** lives in the ML venv — `source ~/ml-env/bin/activate` before the analyzer.
- **Where PDFs go:** `--publish` → `sessions/<slug>/<slug>.pdf` (committed; ~250 KB for an 8-page handout). Anything else → `pdf/` (gitignored scratch).
- **Prose tables: use `{: .ff-wrap}` alone.** `.ff-table` exists to grey and centre Session 2's day-number column, and `.ff-wrap` does not cancel the grey — so `{: .ff-table .ff-wrap}` renders a table's whole second column faint and centred. Check tables in the page images.
- This skill targets a single session page. To prep several, run the `--local` loop per slug — no deploy between them.
- **Preview server down?** `sudo systemctl restart genesis-preview.service` (logs: `journalctl -u genesis-preview.service`). If `--local` renders fail to connect, that service isn't running.
