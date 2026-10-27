# Encodes each recorded segment to constant 30 fps (resampled on the film clock), joins segments with crossfades,
# burns in captions and adds the mix. Usage: python assemble.py segs   (one encode per segment: <tmp>/<seg>.mp4)
#                 python assemble.py segs P3 (re-encode only these segments)
#                 python assemble.py final  (xfade + captions + audio -> <tmp>/<output.file>)
#                 python assemble.py all
# The final encode of a 3.5 min film takes several minutes: run it as a background job.
# Run from the build folder: the captions and their fonts are passed to libass as relative paths, which avoids
# escaping a Windows drive letter inside the filter graph.
import json
import math
import os
import subprocess
import sys
from pathlib import Path

from filmcfg import ffmpeg, load, run_ffmpeg, tmp

cfg = load()
plan = json.load(open(cfg["plan"], encoding="utf-8")); X = plan["X"]
step = sys.argv[1] if len(sys.argv) > 1 else "all"
only = sys.argv[2:]


def esc(p):
    """A path as a filter-graph argument: forward slashes, colons and quotes escaped."""
    return Path(p).as_posix().replace("\\", "/").replace(":", r"\:").replace("'", r"\'")


if step in ("segs", "all"):
    FPS = 30
    for s in plan["segments"]:
        if only and s["name"] not in only:
            continue
        fdir = tmp(cfg, f"frames_{s['name']}")
        m = json.load(open(os.path.join(fdir, "meta.json"), encoding="utf-8")); dur = s["dur"]
        R = m.get("rate", cfg["capture"]["rate"])
        ft = [(t - m["T0"]) * R for t in m["ts"]]          # frame times back on the film clock
        # Constant frame rate by resampling: output frame k (at k/FPS) shows the latest capture at or before it.
        # (Per-frame durations in a concat list stretch the timeline when captures come faster than 25 a second.)
        j = max([i for i, t in enumerate(ft) if t <= 0] or [0])
        p = subprocess.Popen([ffmpeg(cfg), "-hide_banner", "-loglevel", "error", "-y", "-f", "image2pipe",
                              "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-", "-vf", "format=yuv420p", "-t", str(dur),
                              "-c:v", "libx264", "-preset", "ultrafast", "-crf", "12", tmp(cfg, f"{s['name']}.mp4")],
                             stdin=subprocess.PIPE)
        cur = None; data = b""
        for k in range(int(math.ceil(dur * FPS)) + 1):
            while j + 1 < len(ft) and ft[j + 1] <= k / FPS:
                j += 1
            if j != cur:
                cur = j; data = Path(fdir, f"{j + 1:06d}.jpg").read_bytes()
            p.stdin.write(data)
        p.stdin.close()
        if p.wait():
            raise SystemExit(f"encode failed for {s['name']}")
        print("seg", s["name"], "ok", flush=True)
if step in ("final", "all"):
    segs = plan["segments"]; inputs = []
    for s in segs:
        inputs += ["-i", tmp(cfg, f"{s['name']}.mp4")]
    inputs += ["-i", tmp(cfg, cfg["mix"]["file"])]
    fc = ""; prev = "[0:v]"
    for k in range(1, len(segs)):
        out = f"[x{k}]"; fc += f"{prev}[{k}:v]xfade=transition=fade:duration={X}:offset={segs[k]['start']}{out};"; prev = out
    CP = cfg["captions"]
    if CP.get("enabled", True):
        fc += f"{prev}subtitles={esc(CP['file'])}:fontsdir={esc(CP['fontsdir'])}[v]"
    else:
        fc += f"{prev}null[v]"
    O = cfg["output"]; dest = tmp(cfg, O["file"])
    run_ffmpeg(cfg, ["-loglevel", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[v]", "-map", f"{len(segs)}:a",
                     "-c:v", "libx264", "-preset", O["preset"], "-crf", str(O["crf"]), "-profile:v", "high",
                     "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", f"{O['audio_kbps']}k", "-t", str(plan["total"]),
                     "-movflags", "+faststart", dest])
    print("final ok ->", dest, round(os.path.getsize(dest) / 1e6, 1), "MB")
