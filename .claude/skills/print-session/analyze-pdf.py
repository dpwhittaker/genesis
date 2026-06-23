#!/usr/bin/env python3
"""Analyze a genesis handout PDF for page density and section placement.

Counterpart to handout-to-pdf.js. Reads the rendered PDF and reports, per page,
how full it is and which section it starts with — so page breaks can be placed
where sections actually fall, not where source line-counting guesses.

Usage:
    source ~/ml-env/bin/activate      # pymupdf lives here
    python3 .claude/skills/print-session/analyze-pdf.py pdf/01-the-neighbors-stories.pdf

Per page it reports: vertical fullness %, character count, and the first heading.
Warns on sparse pages (<25% — a section is probably overflowing from the page
before) and on overfull pages (>97% — content may be getting clipped). Prints the
total page count and whether it is even (handouts print double-sided; an odd
count wastes a blank back page).

Exit code 0 = no warnings, 1 = warnings found.
"""

import sys
import fitz  # pymupdf

MARGIN_PT = 36.0          # 0.5in margins baked in by the PDF renderer
SPARSE = 0.25             # below this fullness -> warn (section overflow)
OVERFULL = 0.97           # above this -> warn (possible clipping)
BODY_PT = 12.0            # spans larger than this are treated as headings


def page_report(page):
    rect = page.rect
    usable_h = rect.height - 2 * MARGIN_PT
    top, bottom = None, None
    char_count = 0
    first_heading = None

    d = page.get_text("dict")
    for block in d.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue
                char_count += len(text)
                y0, y1 = span["bbox"][1], span["bbox"][3]
                top = y0 if top is None else min(top, y0)
                bottom = y1 if bottom is None else max(bottom, y1)
                if first_heading is None and span.get("size", 0) > BODY_PT:
                    first_heading = text

    if first_heading is None:
        # fall back to the first non-empty line of text
        txt = page.get_text("text").strip().splitlines()
        first_heading = txt[0][:70] if txt else "(blank)"

    if top is None:
        fullness = 0.0
    else:
        fullness = max(0.0, min(1.0, (bottom - MARGIN_PT) / usable_h))

    return {"fullness": fullness, "chars": char_count, "heading": first_heading}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze-pdf.py <file.pdf>", file=sys.stderr)
        sys.exit(2)

    doc = fitz.open(sys.argv[1])
    n = doc.page_count
    warnings = []

    print(f"{sys.argv[1]} — {n} page{'s' if n != 1 else ''}\n")
    print(f"{'pg':>3}  {'full':>5}  {'chars':>6}  heading")
    print("-" * 64)
    for i, page in enumerate(doc, start=1):
        r = page_report(page)
        pct = f"{r['fullness'] * 100:4.0f}%"
        flag = ""
        # A near-empty final page is fine; a sparse interior page means overflow.
        if r["fullness"] < SPARSE and i != n:
            flag = "  <- sparse: section likely overflows from previous page"
            warnings.append((i, "sparse"))
        elif r["fullness"] > OVERFULL:
            flag = "  <- overfull: content may be clipped"
            warnings.append((i, "overfull"))
        print(f"{i:>3}  {pct:>5}  {r['chars']:>6}  {r['heading'][:60]}{flag}")

    print("-" * 64)
    even = (n % 2 == 0)
    print(f"total pages: {n}  ({'even — good for double-sided' if even else 'odd — wastes a blank back page when printed double-sided'})")
    if warnings:
        print(f"\n{len(warnings)} warning(s): " + ", ".join(f"p{p} {k}" for p, k in warnings))
        sys.exit(1)
    print("\nno warnings — page breaks look clean")
    sys.exit(0)


if __name__ == "__main__":
    main()
