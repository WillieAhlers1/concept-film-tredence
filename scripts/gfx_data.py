# Writes gfx-data.js for graphics.html: window.GFX (text, images, axis, stat chips from film.json "graphics")
# and window.SIM (the simulation data, or null when the film has none). Usage: python gfx_data.py
#
# SIM schema (simdata.json): {"rows": [{"id","name","product","dl" (deadline, hours on the film's clock: 15.0 =
# 3 PM today, 33.5 = 9:30 AM tomorrow, >= axis.no_deadline_from = none),"amt","A": [decision hour per simulated
# day, baseline order], "D": [same, optimized order]}], "fifo": [row index per slot, baseline], "iq": [row index
# per slot, optimized], "totals": {...engine totals...}, "futures": total simulated days}.
# Stat chip "before"/"after" strings may use format fields against the totals, e.g. "{t[today_order][ontime_files]:.1f}
# of 11", so the numbers on screen come from the engine, never typed.
# Images that don't exist are dropped, and graphics.html falls back to flat Tredence colour for them.
import json
import os

from filmcfg import load

cfg = load(); G = cfg["graphics"]
sim = None
if G.get("simdata") and os.path.exists(G["simdata"]):
    sim = json.load(open(G["simdata"], encoding="utf-8"))
ctx = {"t": (sim or {}).get("totals", {}), "sim": sim}


def resolve(v):
    if isinstance(v, str) and "{" in v and sim is not None:
        return v.format(**ctx)
    if isinstance(v, dict):
        return {k: resolve(x) for k, x in v.items()}
    if isinstance(v, list):
        return [resolve(x) for x in v]
    return v


gfx = {k: resolve(v) for k, v in G.items() if k not in ("file", "simdata")}
for need in ("night", "morning"):
    assert need in gfx, f'film.json "graphics" needs a "{need}" block (see templates/film.json)'
imgs = gfx.get("images") or {}
missing = [k for k, p in imgs.items() if not (p and os.path.exists(p))]
gfx["images"] = {k: p for k, p in imgs.items() if k not in missing}
if sim is None:
    gfx.pop("sim", None)
with open("gfx-data.js", "w", encoding="utf-8") as f:
    f.write("window.GFX = " + json.dumps(gfx, ensure_ascii=False) + ";\n")
    f.write("window.SIM = " + (json.dumps(sim, separators=(",", ":")) if sim else "null") + ";\n")
print("gfx-data.js:", f"{len(sim['rows'])} rows, {len(sim['rows'][0]['A'])} days per order" if sim else "no simulation",
      "| images missing (flat colour used):", ", ".join(missing) or "none")
