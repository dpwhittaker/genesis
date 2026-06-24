#!/usr/bin/env node
/*
 * groupme-post.js — post one message to the group's GroupMe via the REST API.
 *
 * Usage:
 *   node groupme-post.js "message text"        # text from args
 *   echo "text" | node groupme-post.js         # text from stdin
 *   node groupme-post.js --dry-run "text"      # print, don't send
 *
 * Config (NEVER committed — lives outside the public repo):
 *   GROUPME_TOKEN, GROUPME_GROUP_ID from the environment, else parsed from
 *   ~/.config/genesis/publish.env  (KEY=VALUE lines).
 * The token is a secret. Keep it in ~/.config only; this script is in a public repo.
 *
 * GroupMe API: POST /v3/groups/:id/messages?token=...  (HTTP 201 on success).
 */
const fs = require('fs');
const os = require('os');
const path = require('path');

function loadConfig() {
  const cfg = {};
  const f = path.join(os.homedir(), '.config', 'genesis', 'publish.env');
  if (fs.existsSync(f)) {
    for (const line of fs.readFileSync(f, 'utf8').split('\n')) {
      const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/);
      if (m) cfg[m[1]] = m[2].replace(/^["']|["']$/g, '');
    }
  }
  // Real environment variables win over the file.
  return { ...cfg, ...process.env };
}

async function main() {
  const argv = process.argv.slice(2);
  const dry = argv.includes('--dry-run');
  let text = argv.filter((a) => a !== '--dry-run').join(' ').trim();
  if (!text && !process.stdin.isTTY) text = fs.readFileSync(0, 'utf8').trim();
  if (!text) { console.error('No message text given.'); process.exit(1); }
  if (text.length > 1000) console.error(`Warning: ${text.length} chars; GroupMe truncates at 1000.`);

  const cfg = loadConfig();
  const gid = cfg.GROUPME_GROUP_ID;
  if (!gid) { console.error('GROUPME_GROUP_ID not set (env or ~/.config/genesis/publish.env).'); process.exit(1); }

  if (dry) {
    console.log(`[dry-run] would post to GroupMe group ${gid}:\n---\n${text}\n---`);
    return;
  }

  const token = cfg.GROUPME_TOKEN;
  if (!token) {
    console.error('GROUPME_TOKEN not set. Add it to ~/.config/genesis/publish.env (get one at dev.groupme.com).');
    process.exit(1);
  }

  const sourceGuid = `genesis-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const url = `https://api.groupme.com/v3/groups/${gid}/messages?token=${encodeURIComponent(token)}`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: { source_guid: sourceGuid, text } }),
  });
  if (res.status === 201) {
    const body = await res.json().catch(() => ({}));
    const id = body && body.response && body.response.message && body.response.message.id;
    console.log(`Posted to GroupMe group ${gid}${id ? ` (message id ${id})` : ''}.`);
  } else {
    console.error(`GroupMe POST failed: HTTP ${res.status} — ${await res.text()}`);
    process.exit(1);
  }
}

main().catch((e) => { console.error(e.message || e); process.exit(1); });
