#!/usr/bin/env bash
# queue-audio-js.sh [--dry-run] <long-focus.txt> <short-focus.txt>
#
# Print a script for ONE javascript_tool call on an open Gemini Notebook
# (NotebookLM) notebook: it queues the lesson's two Deep Dive episodes, the Long
# preset with the first focus prompt and the Default preset with the second.
# See queue-audio.js. --dry-run fills and checks both dialogs but generates nothing.
set -euo pipefail

dry=false
[ "${1:-}" = --dry-run ] && { dry=true; shift; }
usage="usage: queue-audio-js.sh [--dry-run] <long-focus.txt> <short-focus.txt>"
long="${1:?$usage}"
short="${2:?$usage}"
here="$(cd "$(dirname "$0")" && pwd)"

# The user's standing instruction for every focus prompt (SKILL.md, step 6).
say='Say Bible references aloud as chapter then verse: "Genesis twelve three" for Genesis 12:3, never "twelve point three".'

# A focus file as a JSON string: trailing whitespace dropped, the pronunciation
# line appended if it is missing, and the dialog's 5000-character cap checked.
focus() {
  grep -qF 'twelve point three' "$1" || echo "note: $1 lacks the pronunciation line; appending it" >&2
  jq -Rs --arg say "$say" --arg f "$1" '
    sub("\\s+$"; "") as $t
    | if $t == "" then error("\($f) is empty") else
        (if ($t | contains("twelve point three")) then $t else $t + " " + $say end) as $p
        | if ($p | length) > 5000
          then error("\($f): \($p | length) characters, but the focus box takes at most 5000")
          else $p end
      end' "$1"
}
lf="$(focus "$long")"
sf="$(focus "$short")"

printf 'const CONFIG = {dryRun: %s, episodes: [{name: "long", length: "Long", focus: %s}, {name: "short", length: "Default", focus: %s}]};\n' \
  "$dry" "$lf" "$sf"
sed -n '/^const sleep = /,$p' "$here/queue-audio.js"
