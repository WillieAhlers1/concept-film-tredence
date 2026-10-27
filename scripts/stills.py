"""Stills of the graphics segments at chosen times (?seek=), to check layout before filming.

Usage: python stills.py [outDir]   (default ./stills; reads film.json "review.stills" {seg: [seconds...]} and
plan.json params; without review.stills, one still every 3 s through each graphics segment). Writes
st_<seg>_<t>.png. Needs Python Playwright; the Node fallback is stills.js.
"""
import asyncio
import json
import sys
from pathlib import Path
from urllib.parse import urlencode

from filmcfg import load
from record import launch


async def main(out):
    from playwright.async_api import async_playwright
    cfg = load(); plan = json.load(open(cfg["plan"], encoding="utf-8"))
    gfx = Path(cfg["graphics"]["file"]).resolve().as_uri()
    want = cfg["review"].get("stills") or {}
    Path(out).mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        b = await launch(pw, cfg, ["--force-device-scale-factor=1", "--hide-scrollbars"])
        p = await b.new_page(viewport={"width": 1920, "height": 1080})
        for seg in [s for s in plan["segments"] if s["kind"] == "gfx"]:
            ts = want.get(seg["seg"]) or [round(t + 1.0, 1) for t in range(0, int(seg["dur"]), 3)]
            q = urlencode({"seg": seg["seg"], **{k: str(v) for k, v in seg["params"].items()}})
            for t in ts:
                await p.goto(f"{gfx}?{q}&seek={t}")
                await p.evaluate("document.fonts.ready")
                await p.wait_for_timeout(700)
                f = Path(out, f"st_{seg['name']}_{seg['seg']}_{t}.png")
                await p.screenshot(path=str(f)); print(f)
        await b.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "stills"))
