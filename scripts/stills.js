// Node fallback for stills.py: stills of the graphics segments at chosen times (?seek=).
// Usage: node stills.js [outDir]   (reads film.json "review.stills" and plan.json params). Writes st_<seg>_<t>.png.
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const { config, launch } = require('./record.js');

const cfgFile = process.env.FILM_CONFIG || 'film.json';
const raw = fs.existsSync(cfgFile) ? JSON.parse(fs.readFileSync(cfgFile, 'utf8')) : {};
const cfg = config();
const plan = JSON.parse(fs.readFileSync(cfg.plan, 'utf8'));
const gfx = pathToFileURL(path.resolve(cfg.gfxFile)).href;
const outDir = process.argv[2] || 'stills';
(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const b = await launch(cfg, ['--force-device-scale-factor=1', '--hide-scrollbars']);
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  const want = (raw.review || {}).stills || {};
  for (const seg of plan.segments.filter(s => s.kind === 'gfx')) {
    let ts = want[seg.seg];
    if (!ts) { ts = []; for (let t = 1; t < seg.dur; t += 3) ts.push(Math.round(t * 10) / 10); }
    const q = new URLSearchParams({ seg: seg.seg, ...Object.fromEntries(Object.entries(seg.params).map(([k, v]) => [k, String(v)])) });
    for (const t of ts) {
      await p.goto(`${gfx}?${q}&seek=${t}`);
      await p.evaluate(() => document.fonts.ready);
      await p.waitForTimeout(700);
      const f = path.join(outDir, `st_${seg.name}_${seg.seg}_${t}.png`);
      await p.screenshot({ path: f });
      console.log(f);
    }
  }
  await b.close();
})();
