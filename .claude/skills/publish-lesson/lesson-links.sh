#!/usr/bin/env bash
# lesson-links.sh — print the canonical published link set for a lesson:
# the session page URL plus every media link the README lists under that lesson
# (short podcast, long podcast, and any other media linked on the lesson line).
#
# Usage: lesson-links.sh <session-slug>
#   e.g. lesson-links.sh 01-the-neighbors-stories
#
# Base URL comes from GENESIS_PAGES_BASE (env or ~/.config/genesis/publish.env),
# defaulting to the live Pages site.
set -euo pipefail

slug="${1:?usage: lesson-links.sh <session-slug>}"
root="$(git rev-parse --show-toplevel)"

cfg="$HOME/.config/genesis/publish.env"
[ -f "$cfg" ] && { set -a; . "$cfg"; set +a; }
base="${GENESIS_PAGES_BASE:-https://dpwhittaker.github.io/genesis}"
base="${base%/}"

readme="$root/README.md"
[ -f "$readme" ] || { echo "no README.md at repo root" >&2; exit 1; }

echo "session    $base/sessions/$slug/"

# Every markdown link target on the README lines that mention this lesson,
# keeping only the ones that point under the lesson's own folder (its media).
grep -E "sessions/$slug/" "$readme" \
  | grep -oE '\]\([^)]+\)' | sed -E 's/^\]\(//; s/\)$//' \
  | grep -E "sessions/$slug/." | sort -u \
  | while read -r rel; do
      rel="${rel#./}"
      echo "media      $base/$rel"
    done

echo "--- local media files present in sessions/$slug/ ---"
find "$root/sessions/$slug" -maxdepth 1 -type f \
  \( -iname '*.m4a' -o -iname '*.mp3' -o -iname '*.mp4' -o -iname '*.pdf' -o -iname '*.m4v' \) \
  -printf '%f\n' 2>/dev/null | sort || true
