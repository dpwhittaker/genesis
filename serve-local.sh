#!/usr/bin/env bash
# Serve the genesis site locally the way GitHub Pages serves it: same minima
# theme, same kramdown, same "/genesis" baseurl. This lets the print-session
# skill render the handout layout from localhost instead of waiting ~90s for a
# Pages deploy on every page-break tweak.
#
#   ./serve-local.sh              # serve at http://127.0.0.1:4000/genesis/
#   ./serve-local.sh 4010         # custom port
#
# Runs in the foreground (so systemd or the caller can manage it). Uses
# Gemfile.local (invisible to the Pages build) and a project-local
# vendor/bundle, so nothing here can affect how the live site is built.
set -euo pipefail
cd "$(dirname "$0")"
PORT="${1:-4000}"
export BUNDLE_GEMFILE=Gemfile.local
exec bundle exec jekyll serve \
  --baseurl /genesis \
  --host 127.0.0.1 --port "$PORT"
