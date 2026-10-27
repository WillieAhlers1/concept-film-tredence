# Places each narration cue at its planned time, normalises the voice, ducks the music under it and limits.
# Usage: python mix.py   (reads film.json, plan.json, the narration audio and music.wav; writes <tmp>/<mix.file>)
# Targets: voice about -18 dB mean, music alone about -27 to -31 dB (check with: python mix.py --levels).
import json
import re
import sys

from filmcfg import load, run_ffmpeg, tmp

cfg = load(); MX = cfg["mix"]
plan = json.load(open(cfg["plan"], encoding="utf-8"))
out_wav = tmp(cfg, MX["file"])


def level(args):
    log = run_ffmpeg(cfg, [*args, "-f", "null", "-"], check=False).stderr
    mv = re.search(r"mean_volume: ([-\d.]+)", log); pk = re.search(r"max_volume: ([-\d.]+)", log)
    return f"mean {mv and mv.group(1)} dB, max {pk and pk.group(1)} dB"


if "--levels" in sys.argv:      # the mix is dominated by the voice; the music is measured alone at its mix gain
    print("mix (voice):", level(["-i", out_wav, "-af", "volumedetect"]))
    print("music alone:", level(["-i", cfg["music"]["file"], "-af", f"volume={MX['music_db']}dB,volumedetect"]))
    raise SystemExit

parts = []; labels = []
for i, c in enumerate(plan["cues"]):
    a, b = c["src"]; d = int(round(c["at"] * 1000))
    parts.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,adelay={d}|{d}[n{i}]")
    labels.append(f"[n{i}]")
fc = ";".join(parts) + ";" + "".join(labels) + f"amix=inputs={len(labels)}:normalize=0,apad=whole_dur={plan['total'] + cfg['music'].get('tail_s', 2.5)},loudnorm=I={MX['voice_lufs']}:TP=-2:LRA=7[voice];"
fc += f"[voice]asplit=2[v1][v2];[1:a]volume={MX['music_db']}dB[m];[m][v2]sidechaincompress=threshold=0.02:ratio=4:attack=40:release=700[md];"
fc += f"[v1][md]amix=inputs=2:normalize=0,alimiter=limit={MX['limit']}[out]"
open("mix_fc.txt", "w", encoding="utf-8").write(fc)
run_ffmpeg(cfg, ["-loglevel", "error", "-y", "-i", cfg["narration"]["audio"], "-i", cfg["music"]["file"],
                 "-filter_complex", fc, "-map", "[out]", "-ar", "48000", "-c:a", "pcm_s16le", out_wav])
print("mix ->", out_wav)
