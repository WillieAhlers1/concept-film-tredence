"""Films one segment of the film and writes JPEG frames plus meta.json to <tmp>/frames_<segment>.

Usage: python record.py <segmentName>      (reads film.json + plan.json; run from the build folder)

Page time runs at capture.rate (default 0.25: four times slower) through slowtime.js and CDP
Animation.setPlaybackRate, and frames come from a CDP screencast, so every animation is captured smoothly however
slow the machine is; assemble.py maps the frames back onto the film clock. Prototype segments wait for the engine
warm-up, hide the presenter chrome (film_css), press the hide-cues key, replay the scene opened by #hash, then press
the next key on the plan's schedule. Graphics segments call window.start().
Needs Python Playwright (pip install playwright). Without it, use the Node fallback record.js.
"""
import asyncio
import base64
import json
import os
import shutil
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

from filmcfg import load

HERE = Path(__file__).resolve().parent


def find_docgen_shell():
    root = Path("/opt/docgen-browsers")
    if not root.exists():
        return None
    d = sorted(x for x in os.listdir(root) if x.startswith("chromium_headless_shell-"))
    return str(root / d[-1] / "chrome-headless-shell-linux64" / "chrome-headless-shell") if d else None


async def launch(pw, cfg, args):
    exe = os.environ.get("CHR") or cfg["capture"].get("chrome")
    if exe:
        return await pw.chromium.launch(executable_path=exe, args=args)
    errors = []
    for opts in ({}, {"channel": "msedge"}, {"channel": "chrome"}, {"executable_path": find_docgen_shell()}):
        if "executable_path" in opts and not opts["executable_path"]:
            continue
        try:
            return await pw.chromium.launch(args=args, **opts)
        except Exception as e:  # try the next browser
            errors.append(f"{opts or 'playwright chromium'}: {str(e).splitlines()[0]}")
    raise SystemExit("no browser for Playwright: " + " | ".join(errors) + "  (run: python -m playwright install chromium)")


def page_url(cfg, seg):
    if seg["kind"] == "proto":
        p = Path(cfg["prototype"]["dir"], cfg["prototype"]["file"]).resolve()
        return p.as_uri() + (seg.get("hash") or "")
    q = urlencode({"seg": seg["seg"], **{k: str(v) for k, v in seg["params"].items()}})
    return Path(cfg["graphics"]["file"]).resolve().as_uri() + "?" + q


def init_script(cfg, rate):
    css = json.dumps(cfg["prototype"].get("film_css") or "")
    return (f"window.__RATE__={rate};" + (HERE / "slowtime.js").read_text(encoding="utf-8") +
            f";(()=>{{const css={css};if(!css)return;const add=()=>{{const s=document.createElement('style');"
            "s.textContent=css;(document.head||document.documentElement).appendChild(s);};"
            "if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',add);else add();})();")


async def record(name):
    from playwright.async_api import async_playwright
    cfg = load(); C = cfg["capture"]; PR = cfg["prototype"]; K = PR["keys"]; RATE = C["rate"]
    plan = json.load(open(cfg["plan"], encoding="utf-8"))
    seg = next((s for s in plan["segments"] if s["name"] == name), None)
    if not seg:
        raise SystemExit(f"no segment {name} in {cfg['plan']}")
    out = Path(cfg["tmp"], f"frames_{name}")
    shutil.rmtree(out, ignore_errors=True); out.mkdir(parents=True)
    async with async_playwright() as pw:
        b = await launch(pw, cfg, ["--force-device-scale-factor=1", "--hide-scrollbars"])
        p = await b.new_page(viewport={"width": C["width"], "height": C["height"]})
        await p.add_init_script(init_script(cfg, RATE))
        await p.goto(page_url(cfg, seg))
        s = await p.context.new_cdp_session(p)
        await s.send("Animation.enable"); await s.send("Animation.setPlaybackRate", {"playbackRate": RATE})
        await asyncio.sleep(PR["warmup_s"] if seg["kind"] == "proto" else C["gfx_settle_ms"] / 1000)
        if seg["kind"] == "proto" and K.get("hide"):
            await p.keyboard.press(K["hide"])          # presenter click cues off
        ts = []; n = 0; pending = set()

        def on_frame(f):
            nonlocal n
            n += 1; ts.append(f["metadata"]["timestamp"])
            (out / f"{n:06d}.jpg").write_bytes(base64.b64decode(f["data"]))
            t = asyncio.ensure_future(s.send("Page.screencastFrameAck", {"sessionId": f["sessionId"]}))
            pending.add(t); t.add_done_callback(pending.discard)

        s.on("Page.screencastFrame", on_frame)
        await s.send("Page.startScreencast", {"format": "jpeg", "quality": C["jpeg_quality"],
                                             "maxWidth": C["width"], "maxHeight": C["height"]})
        await asyncio.sleep(C["pre_roll_ms"] / 1000)
        T0 = time.time()
        if seg["kind"] == "gfx":
            await p.evaluate("() => window.start()")
        elif seg.get("replay") and K.get("replay"):
            await p.keyboard.press(K["replay"])        # replay the scene opened by #hash from its first beat
        for t in seg.get("presses") or []:
            w = T0 + t / RATE - time.time()
            if w > 0:
                await asyncio.sleep(w)
            await p.keyboard.press(K["next"])
        end_due = T0 + (seg["dur"] + 0.4) / RATE - time.time()
        if end_due > 0:
            await asyncio.sleep(end_due)
        await s.send("Page.stopScreencast")
        await asyncio.sleep(0.2)
        (out / "meta.json").write_text(json.dumps({"T0": T0, "ts": ts, "dur": seg["dur"], "rate": RATE}), encoding="utf-8")
        print(name, "frames", n, flush=True)
        await b.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: python record.py <segmentName>")
    asyncio.run(record(sys.argv[1]))
