"""Films every segment in plan.json, one after another (graphics first, they are quick), logging to one file.

Usage: python record_all.py [logFile] [SEG ...]     (default log: <tmp>/rec_all.log; default: every segment)
Run it as a background job; the log ends with ALLDONE. Progress: count the JPEGs in <tmp>/frames_<SEG>.
A 3.5 min film takes about 15 min. Uses record.py (Python Playwright), else node record.js.
"""
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from filmcfg import load

HERE = Path(__file__).resolve().parent
cfg = load()
log = sys.argv[1] if len(sys.argv) > 1 else os.path.join(cfg["tmp"], "rec_all.log")
want = sys.argv[2:]
segs = json.load(open(cfg["plan"], encoding="utf-8"))["segments"]
order = [s["name"] for s in segs if s["kind"] == "gfx"] + [s["name"] for s in segs if s["kind"] != "gfx"]
order = [s for s in order if not want or s in want]
if importlib.util.find_spec("playwright"):
    cmd = [sys.executable, str(HERE / "record.py")]
else:
    cmd = ["node", str(HERE / "record.js")]
with open(log, "a", encoding="utf-8") as L:
    for s in order:
        L.write(f"start {s} {time.strftime('%H:%M:%S')}\n"); L.flush()
        r = subprocess.run(cmd + [s], stdout=L, stderr=subprocess.STDOUT)
        if r.returncode:
            L.write(f"FAILED {s} exit {r.returncode}\n"); L.flush()
            print("FAILED", s, "- see", log); sys.exit(1)
        print("filmed", s, flush=True)
    L.write("ALLDONE\n")
print("ALLDONE ->", log)
