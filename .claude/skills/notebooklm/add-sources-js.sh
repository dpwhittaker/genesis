#!/usr/bin/env bash
# add-sources-js.sh <slug>
#
# Print a script for ONE javascript_tool call on an open Gemini Notebook
# (NotebookLM) notebook: it fetches the lesson's handout and source sheets from
# the public repo at the current commit, cleans them exactly as prep-sources.sh
# does, and adds each as a "Copied text" source. See add-sources.js.
#
# The sources must be committed and pushed first: the browser fetches them from
# raw.githubusercontent.com, pinned to HEAD's SHA.
set -euo pipefail

slug="${1:?usage: add-sources-js.sh <slug>}"
here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/../../.." && pwd)"
sess="sessions/$slug"
cd "$root"
[ -f "$sess/index.md" ] || { echo "no such session: $sess" >&2; exit 1; }

if [ -n "$(git status --porcelain -- "$sess")" ]; then
  echo "$sess has uncommitted changes; commit and push them first:" >&2
  git status --short -- "$sess" >&2
  exit 1
fi
sha="$(git rev-parse HEAD)"
git branch -r --contains "$sha" | grep -qx '  origin/main' \
  || { echo "HEAD ($sha) is not on origin/main yet; push first" >&2; exit 1; }
repo="$(git remote get-url origin | sed -E 's#^(git@github\.com:|https://github\.com/)##; s#\.git$##')"

# Expected sizes come from prep-sources.sh itself, so the browser-side cleaning
# is checked against it file by file. Its order: handout, other top-level pages,
# then texts/.
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
files=()
while IFS= read -r txt; do
  name="$(basename "$txt" .txt)"; name="${name#"${slug}__"}"
  case "$name" in
    handout) md="index.md" ;;
    text__*) md="texts/${name#text__}.md" ;;
    *)       md="$name.md" ;;
  esac
  [ -f "$sess/$md" ] || { echo "can't map $txt back to a file in $sess" >&2; exit 1; }
  files+=("{\"path\":\"$md\",\"bytes\":$(wc -c < "$txt")}")
done < <("$here/prep-sources.sh" "$slug" "$tmp")

printf 'const CONFIG = {base: "https://raw.githubusercontent.com/%s/%s/%s/", files: [%s]};\n' \
  "$repo" "$sha" "$sess" "$(IFS=,; echo "${files[*]}")"
sed -n '/^const clean = /,$p' "$here/add-sources.js"
