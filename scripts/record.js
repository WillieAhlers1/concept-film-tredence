// Node fallback for record.py (use it where Python Playwright is missing but Node Playwright is installed, for
// example a sandbox with docgen-utils). Same behaviour: films one segment at page-time rate capture.rate and
// writes JPEG frames plus meta.json to <tmp>/frames_<segment>.  Usage: node record.js <segmentName>
let chromium;
try { ({ chromium } = require('playwright')); } catch (e) { ({ chromium } = require('/usr/local/lib/node_modules/docgen-utils/node_modules/playwright')); }
const fs = require('fs');
const os = require('os');
const path = require('path');
const { pathToFileURL } = require('url');

const FILM_CSS = '.proto-nav,.proto-next,.proto-dots,.proto-notes,.proto-help{display:none!important}' +
  '.cue{outline:none!important;box-shadow:none!important}';

function config() {
  const f = process.env.FILM_CONFIG || 'film.json';
  const c = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')) : {};
  const cap = c.capture || {}, pr = c.prototype || {}, keys = pr.keys || {}, g = c.graphics || {};
  return {
    tmp: c.tmp || path.join(os.tmpdir(), 'film-work'), plan: c.plan || 'plan.json',
    rate: cap.rate || 0.25, w: cap.width || 1920, h: cap.height || 1080, q: cap.jpeg_quality || 86,
    gfxSettle: cap.gfx_settle_ms ?? 4000, preRoll: cap.pre_roll_ms ?? 1500, chrome: cap.chrome || '',
    protoDir: pr.dir || 'proto', protoFile: pr.file || 'prototype.html', warmup: (pr.warmup_s ?? 30) * 1000,
    filmCss: pr.film_css ?? FILM_CSS,
    kHide: keys.hide ?? 'h', kReplay: keys.replay ?? 'r', kNext: keys.next || 'ArrowRight',
    gfxFile: g.file || 'graphics.html',
  };
}
async function launch(cfg, args) {
  const exe = process.env.CHR || cfg.chrome;
  if (exe) return chromium.launch({ executablePath: exe, args });
  const tries = [{}, { channel: 'msedge' }, { channel: 'chrome' }];
  const root = '/opt/docgen-browsers';
  if (fs.existsSync(root)) {
    const d = fs.readdirSync(root).filter(x => x.startsWith('chromium_headless_shell-')).sort().pop();
    if (d) tries.push({ executablePath: path.join(root, d, 'chrome-headless-shell-linux64', 'chrome-headless-shell') });
  }
  for (const t of tries) { try { return await chromium.launch({ args, ...t }); } catch (e) { /* next */ } }
  throw new Error('no browser for Playwright');
}
module.exports = { config, launch };

if (require.main === module) (async () => {
  const cfg = config(), RATE = cfg.rate;
  const plan = JSON.parse(fs.readFileSync(cfg.plan, 'utf8'));
  const seg = plan.segments.find(s => s.name === process.argv[2]);
  if (!seg) throw new Error(`no segment ${process.argv[2]} in ${cfg.plan}`);
  const OUT = path.join(cfg.tmp, `frames_${seg.name}`);
  fs.rmSync(OUT, { recursive: true, force: true }); fs.mkdirSync(OUT, { recursive: true });
  const b = await launch(cfg, ['--force-device-scale-factor=1', '--hide-scrollbars']);
  const p = await b.newPage({ viewport: { width: cfg.w, height: cfg.h } });
  const css = JSON.stringify(cfg.filmCss || '');
  await p.addInitScript(`window.__RATE__=${RATE};` + fs.readFileSync(path.join(__dirname, 'slowtime.js'), 'utf8') +
    `;(()=>{const css=${css};if(!css)return;const add=()=>{const s=document.createElement('style');s.textContent=css;` +
    `(document.head||document.documentElement).appendChild(s);};if(document.readyState==='loading')` +
    `document.addEventListener('DOMContentLoaded',add);else add();})();`);
  let url;
  if (seg.kind === 'proto') url = pathToFileURL(path.resolve(cfg.protoDir, cfg.protoFile)).href + (seg.hash ?? '');
  else url = pathToFileURL(path.resolve(cfg.gfxFile)).href + '?' + new URLSearchParams({ seg: seg.seg, ...Object.fromEntries(Object.entries(seg.params).map(([k, v]) => [k, String(v)])) });
  await p.goto(url);
  const s = await p.context().newCDPSession(p);
  await s.send('Animation.enable'); await s.send('Animation.setPlaybackRate', { playbackRate: RATE });
  await p.waitForTimeout(seg.kind === 'proto' ? cfg.warmup : cfg.gfxSettle);
  if (seg.kind === 'proto' && cfg.kHide) await p.keyboard.press(cfg.kHide);
  const ts = []; let n = 0;
  s.on('Page.screencastFrame', f => {
    n++; ts.push(f.metadata.timestamp);
    fs.writeFileSync(path.join(OUT, `${String(n).padStart(6, '0')}.jpg`), Buffer.from(f.data, 'base64'));
    s.send('Page.screencastFrameAck', { sessionId: f.sessionId }).catch(() => {});
  });
  await s.send('Page.startScreencast', { format: 'jpeg', quality: cfg.q, maxWidth: cfg.w, maxHeight: cfg.h });
  await p.waitForTimeout(cfg.preRoll);
  const T0 = Date.now();
  if (seg.kind === 'gfx') await p.evaluate(() => window.start());
  else if (seg.replay && cfg.kReplay) await p.keyboard.press(cfg.kReplay);
  for (const t of (seg.presses || [])) {
    const w = T0 + (t / RATE) * 1000 - Date.now(); if (w > 0) await p.waitForTimeout(w);
    await p.keyboard.press(cfg.kNext);
  }
  const endDue = T0 + ((seg.dur + 0.4) / RATE) * 1000; if (endDue > Date.now()) await p.waitForTimeout(endDue - Date.now());
  await s.send('Page.stopScreencast');
  fs.writeFileSync(path.join(OUT, 'meta.json'), JSON.stringify({ T0: T0 / 1000, ts, dur: seg.dur, rate: RATE }));
  console.log(seg.name, 'frames', n);
  await b.close();
})();
