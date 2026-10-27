// Injected before page scripts: runs page time at RATE (e.g. 0.25 = 4x slower) so a slow headless capture plays back smoothly.
// Keep cb(performance.now()) in the rAF wrapper: passing rAF's own (unscaled) timestamp stalls text streaming
// once CDP Animation.setPlaybackRate is also set.
(() => {
  const RATE = window.__RATE__ || 0.25;
  const pn = performance.now.bind(performance), dn = Date.now;
  const p0 = pn(), d0 = dn();
  performance.now = () => p0 + (pn() - p0) * RATE;
  Date.now = () => d0 + (dn() - d0) * RATE;
  const st = window.setTimeout, si = window.setInterval;
  window.setTimeout = (f, ms, ...a) => st(f, (ms || 0) / RATE, ...a);
  window.setInterval = (f, ms, ...a) => si(f, (ms || 0) / RATE, ...a);
  const raf = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = cb => raf(() => cb(performance.now()));
})();
