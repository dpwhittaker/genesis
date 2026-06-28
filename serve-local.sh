#!/usr/bin/env bash
# Serve the genesis site locally the way GitHub Pages serves it: same minima
# theme, same kramdown, same "/genesis" baseurl. This lets the print-session
# skill render the handout layout from localhost instead of waiting ~90s for a
# Pages deploy on every page-break tweak.
#
#   ./serve-local.sh              # serve at http://127.0.0.1:4000/genesis/
#   ./serve-local.sh 4010         # custom port
#
# Runs sync-server.js (a thin Node front): it spawns Jekyll on :4001 with
# Gemfile.local and the /genesis baseurl, reverse-proxies the static site, and
# adds the /genesis/sync/* "remote drive" API for the slideshow. Foreground, so
# systemd or the caller can manage it. Nothing here touches the Pages build.
set -euo pipefail
cd "$(dirname "$0")"
export PORT="${1:-4000}"
exec node sync-server.js
