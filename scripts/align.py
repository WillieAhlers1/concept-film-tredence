# Splits the voiced narration into cue lines -> cues.json (src start/end, duration, text per cue).
# Turn boundaries in the recording are pauses of about 0.53-0.65 s; pauses inside a turn are at most ~0.45 s.
# silencedetect finds every pause, then dynamic programming picks the n-1 boundaries whose segment lengths best
# match the expected durations (characters / speaking rate). Usage: python align.py   (reads film.json)
# Only needed when the narration was voiced in one take elsewhere (for example PodcastGenerate); voice.py writes
# cues.json itself, with exact boundaries.
import json
import re
from filmcfg import load, media_seconds, run_ffmpeg

cfg = load()
NC = cfg["narration"]
log = run_ffmpeg(cfg, ["-i", NC["audio"], "-af",
                      f"silencedetect=noise={NC['silence_noise_db']}dB:d={NC['silence_min_s']}", "-f", "null", "-"]).stderr
st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
total = media_seconds(cfg, NC["audio"])
cands = [(s, e) for s, e in zip(st, en) if s > 0.3 and e < total - 0.3]
P = NC["prefix"]
turns = [l[len(P):].strip() for l in open(NC["transcript"], encoding="utf-8") if l.startswith(P)]
n = len(turns)
ids = NC["cue_ids"] or [f"C{k + 1:02d}" for k in range(n)]
assert len(ids) == n, f"{n} narration lines in {NC['transcript']} but {len(ids)} cue ids in film.json"
assert len(cands) >= n - 1, f"only {len(cands)} pauses found for {n} lines; lower silence_min_s or check the recording"
ch = [len(t) for t in turns]
speech = total - sum(e - s for s, e in cands if e - s > 0.5)
rate = sum(ch) / speech
exp = [c / rate for c in ch]
# DP: choose n-1 boundaries (candidate indices increasing); longer pauses are preferred as boundaries
C = len(cands); INF = 1e18
bpos = [(s + e) / 2 for s, e in cands]; bd = [e - s for s, e in cands]
dp = [[INF] * C for _ in range(n - 1)]; bk = [[-1] * C for _ in range(n - 1)]


def cost(seg, k):
    return (seg - exp[k]) ** 2 / max(exp[k], 1.0)


for j in range(C):
    dp[0][j] = cost(bpos[j] - 0, 0) - 3 * bd[j]
for k in range(1, n - 1):
    for j in range(k, C):
        best = INF; arg = -1
        for i in range(k - 1, j):
            if dp[k - 1][i] >= INF:
                continue
            v = dp[k - 1][i] + cost(bpos[j] - bpos[i], k)
            if v < best:
                best = v; arg = i
        dp[k][j] = best - 3 * bd[j]; bk[k][j] = arg
best = INF; arg = -1
for j in range(C):
    v = dp[n - 2][j] + cost(total - bpos[j], n - 1)
    if v < best:
        best = v; arg = j
idx = [arg]
for k in range(n - 2, 0, -1):
    idx.append(bk[k][idx[-1]])
idx = idx[::-1]
pad = NC["boundary_pad_s"]
segs = []; prev = 0.0
for j in idx:
    s, e = cands[j]; segs.append([round(prev, 3), round(s + pad, 3)]); prev = e - pad
segs.append([round(prev, 3), round(total, 3)])
out = {ids[k]: {"src": segs[k], "dur": round(segs[k][1] - segs[k][0], 3), "text": turns[k]} for k in range(n)}
json.dump(out, open(cfg["cues"], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for k in range(n):
    j = idx[k] if k < n - 1 else None
    print(ids[k], f"{segs[k][1] - segs[k][0]:5.2f} exp {exp[k]:5.2f}", f"gap {bd[j]:.2f}" if j is not None else "", turns[k][:50])
