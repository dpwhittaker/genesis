#!/usr/bin/env node
/* Thin front for the genesis preview.
 *
 * Spawns Jekyll on :4001 and serves the whole static site by reverse-proxying to
 * it, while adding a tiny "remote drive" API at /<baseurl>/sync/* so the
 * slideshow's CURRENT SLIDE can be driven from a phone and mirrored to the TV.
 *
 * This week we only sync which slide we're on (no per-element interactions).
 * State is one integer; clients POST a slide and poll for changes. Polling is
 * deliberately boring — it survives the claude-hub proxy and tailscale with no
 * WebSocket/SSE buffering concerns. No npm dependencies.
 *
 * claude-hub forwards /genesis/* here (stripPrefix:false), so this process sees
 * /genesis/sync/state, /genesis/sync/goto, and /genesis/<everything else>.
 */
const http = require('http');
const { spawn } = require('child_process');

const PORT = Number(process.env.PORT) || 4000;
const JEKYLL_PORT = Number(process.env.JEKYLL_PORT) || 4001;

// ---- Jekyll behind us (same flags as serve-local.sh used to run directly) ----
const jek = spawn('bundle',
  ['exec', 'jekyll', 'serve', '--baseurl', '/genesis', '--host', '127.0.0.1', '--port', String(JEKYLL_PORT)],
  { cwd: __dirname, env: { ...process.env, BUNDLE_GEMFILE: 'Gemfile.local' } });
jek.stdout.on('data', d => process.stdout.write('[jekyll] ' + d));
jek.stderr.on('data', d => process.stderr.write('[jekyll] ' + d));
jek.on('exit', code => { console.error('[front] jekyll exited (' + code + '); exiting so systemd restarts us'); process.exit(1); });
process.on('SIGTERM', () => { try { jek.kill('SIGTERM'); } catch (_) {} process.exit(0); });

// ---- remote-drive state: just the current slide ----
const state = { slide: 0, seq: 0, total: 0, at: Date.now() };
function json(res, code, obj) {
  const b = JSON.stringify(obj);
  res.writeHead(code, { 'content-type': 'application/json', 'cache-control': 'no-store', 'access-control-allow-origin': '*' });
  res.end(b);
}

const server = http.createServer((req, res) => {
  const url = req.url || '/';
  if (url.includes('/sync/')) {
    const route = url.split('/sync/')[1].split('?')[0];
    if (req.method === 'GET' && route === 'state') return json(res, 200, state);
    if (req.method === 'POST' && route === 'goto') {
      let body = '';
      req.on('data', d => { body += d; if (body.length > 1e4) req.destroy(); });
      req.on('end', () => {
        try {
          const j = JSON.parse(body || '{}');
          if (Number.isInteger(j.slide)) { state.slide = j.slide; state.seq++; state.at = Date.now(); }
          if (Number.isInteger(j.total)) state.total = j.total;
        } catch (_) {}
        json(res, 200, state);
      });
      return;
    }
    return json(res, 404, { error: 'sync route not found' });
  }
  // everything else -> Jekyll
  const proxy = http.request(
    { host: '127.0.0.1', port: JEKYLL_PORT, method: req.method, path: url, headers: req.headers },
    pres => { res.writeHead(pres.statusCode || 502, pres.headers); pres.pipe(res); }
  );
  proxy.on('error', () => { res.writeHead(502, { 'content-type': 'text/plain' }); res.end('preview server is starting…'); });
  req.pipe(proxy);
});
server.listen(PORT, '127.0.0.1', () => console.log(`[front] genesis on :${PORT} (jekyll behind on :${JEKYLL_PORT})`));
