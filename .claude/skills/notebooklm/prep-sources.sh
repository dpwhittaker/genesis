#!/usr/bin/env bash
# prep-sources.sh <slug> <outdir>
#
# Produce clean plain-text source files for a Genesis lesson, ready to upload to
# NotebookLM as sources. Strips Jekyll front matter, HTML tags, and kramdown
# inline-attribute lines from the session handout and its primary texts, so
# NotebookLM ingests readable prose instead of markup.
#
# Prints one absolute path per produced file on stdout (feed these to the
# file_upload browser tool). Writes into <outdir> (use the session scratchpad,
# which is upload-eligible).
set -euo pipefail

slug="${1:?usage: prep-sources.sh <slug> <outdir>}"
outdir="${2:?usage: prep-sources.sh <slug> <outdir>}"
root="$(cd "$(dirname "$0")/../../.." && pwd)"   # repo root (.claude/skills/notebooklm -> repo)
sess="$root/sessions/$slug"
[ -d "$sess" ] || { echo "no such session: $sess" >&2; exit 1; }
mkdir -p "$outdir"

# strip: YAML front matter (leading ---..--- block), HTML tags, kramdown {: ...}
# attribute lines, markdown link syntax (keep the visible text), and a few HTML
# entities. Collapse blank runs. Good enough for clean NotebookLM grounding.
clean() {
  awk 'NR==1&&$0=="---"{fm=1;next} fm&&$0=="---"{fm=0;next} !fm' "$1" \
  | sed -E \
      -e 's/<[^>]+>//g' \
      -e 's/^\{:.*\}$//' \
      -e 's/\[([^]]*)\]\([^)]*\)/\1/g' \
      -e 's/&nbsp;/ /g; s/&amp;/\&/g; s/&mdash;/—/g; s/&ldquo;/"/g; s/&rdquo;/"/g' \
  | cat -s
}

produced=()

# 1) the handout
if [ -f "$sess/index.md" ]; then
  out="$outdir/${slug}__handout.txt"
  clean "$sess/index.md" > "$out"
  produced+=("$out")
fi

# 2) primary texts
if [ -d "$sess/texts" ]; then
  for f in "$sess"/texts/*.md; do
    [ -e "$f" ] || continue
    base="$(basename "${f%.md}")"
    out="$outdir/${slug}__text__${base}.txt"
    clean "$f" > "$out"
    produced+=("$out")
  done
fi

[ ${#produced[@]} -gt 0 ] || { echo "nothing produced for $slug" >&2; exit 1; }
printf '%s\n' "${produced[@]}"
