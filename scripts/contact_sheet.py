# Review aid: pulls a frame every ~7 s from the film and lays them out as contact sheets, each frame labelled
# with its time and the narration line playing then, so every frame can be checked against its line, the beat
# state, captions not covering key UI, and missing builds.
# Usage: python contact_sheet.py [film.mp4] [outDir]   (defaults: <tmp>/<output.file>, ./review)
import glob
import json
import os
import shutil
import sys
import textwrap

from PIL import Image, ImageDraw, ImageFont

from filmcfg import load, media_seconds, run_ffmpeg, tmp

cfg = load(); RV = cfg["review"]
video = sys.argv[1] if len(sys.argv) > 1 else tmp(cfg, cfg["output"]["file"])
out = sys.argv[2] if len(sys.argv) > 2 else "review"
every = float(RV["every_s"]); cols, rows = int(RV["cols"]), int(RV["rows"])
fdir = tmp(cfg, "review_frames"); shutil.rmtree(fdir, ignore_errors=True); os.makedirs(fdir); os.makedirs(out, exist_ok=True)
total = media_seconds(cfg, video)
times = []; t = every / 2
while t < total:
    times.append(round(t, 2)); t += every
for i, t in enumerate(times):           # one accurate seek per frame, so each label matches its frame
    run_ffmpeg(cfg, ["-loglevel", "error", "-y", "-ss", str(t), "-i", video, "-frames:v", "1", "-vf", "scale=640:360",
                     "-q:v", "3", os.path.join(fdir, f"f_{i:04d}.jpg")])
cues = json.load(open(cfg["plan"], encoding="utf-8"))["cues"] if os.path.exists(cfg["plan"]) else []


def line_at(t):
    for c in cues:
        if c["at"] <= t <= c["at"] + (c["src"][1] - c["src"][0]):
            return c["id"] + ": " + c["text"]
    return "(no narration)"


font = None
for f in (os.path.join(cfg["captions"]["fontsdir"], "Poppins-Regular.ttf"), "DejaVuSans.ttf", "arial.ttf"):
    try:
        font = ImageFont.truetype(f, 14); break
    except OSError:
        pass
font = font or ImageFont.load_default()
frames = sorted(glob.glob(os.path.join(fdir, "f_*.jpg"))); W, H, TH = 640, 360, 92; per = cols * rows
for s in range(0, len(frames), per):
    used = -(-len(frames[s:s + per]) // cols)
    sheet = Image.new("RGB", (cols * W, used * (H + TH)), "white"); d = ImageDraw.Draw(sheet)
    for k, f in enumerate(frames[s:s + per]):
        i = s + k; t = times[i]; X = (k % cols) * W; Y = (k // cols) * (H + TH)
        sheet.paste(Image.open(f), (X, Y))
        label = f"{int(t // 60)}:{t % 60:04.1f}  " + line_at(t)
        d.multiline_text((X + 6, Y + H + 4), "\n".join(textwrap.wrap(label, 78)[:4]), fill="black", font=font)
    name = os.path.join(out, f"sheet_{s // per + 1:02d}.jpg"); sheet.save(name, quality=85); print(name)
