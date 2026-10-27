# Original ambient score for the film: slow pad, soft bass and a light bell arpeggio, simple room reverb, fades.
# Generated here with numpy, no samples, no licensed material, no imitation of named artists.
# Usage: python music.py   (reads film.json + plan.json; writes music.file, default music.wav)
# Mood levers in film.json "music": seed, chords (MIDI lists), bass (MIDI), bar_s, bell_step_s, bell_gain, lowpass_hz.
import json

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

from filmcfg import load

cfg = load(); M = cfg["music"]
SR = 48000
plan = json.load(open(cfg["plan"], encoding="utf-8")); L = plan["total"] + M.get("tail_s", 2.5)
N = int(L * SR); t = np.arange(N) / SR


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# chords (MIDI): Dmaj9, Bm9, Gmaj9, A6sus  (8 s each); the last bars resolve to the first chord
CH = M.get("chords") or [[50, 57, 61, 64, 66], [47, 54, 57, 61, 62], [43, 50, 54, 57, 62], [45, 50, 52, 54, 59]]
BASS = M.get("bass") or [38, 35, 31, 33]
BAR = float(M.get("bar_s", 8.0))
STEP = float(M.get("bell_step_s", 0.75))      # 80 bpm eighths
BELL = float(M.get("bell_gain", 0.22))
pad = np.zeros((N, 2)); bell = np.zeros((N, 2)); bass = np.zeros(N)
rng = np.random.default_rng(M.get("seed", 7))
nb = int(np.ceil(L / BAR))
end_bar = int((L - 12.5) // BAR)
for k in range(nb):
    ci = 0 if k >= end_bar else k % len(CH)
    s0 = k * BAR; a = int(s0 * SR); e = min(N, int((s0 + BAR + 3.0) * SR))
    tt = t[a:e] - s0
    env = np.clip(tt / 2.5, 0, 1) * np.clip((BAR + 3.0 - tt) / 3.0, 0, 1)
    env = env ** 1.5
    for m in CH[ci]:
        for det, pan in [(-0.06, 0.25), (0.0, 0.5), (0.07, 0.75)]:
            f = hz(m) * 2 ** (det / 12)
            ph = rng.uniform(0, 2 * np.pi)
            v = (np.sin(2 * np.pi * f * tt + ph) + 0.18 * np.sin(4 * np.pi * f * tt + ph)) * env
            pad[a:e, 0] += v * (1 - pan); pad[a:e, 1] += v * pan
    fb = hz(BASS[ci])
    bass[a:e] += np.sin(2 * np.pi * fb * tt) * env * 1.3 + 0.25 * np.sin(4 * np.pi * fb * tt) * env
    # bell arpeggio, left out of the first bar and the last bars
    if 1 <= k < end_bar:
        tones = [n + 12 for n in CH[ci][1:]]
        for j in range(int(BAR / STEP)):
            st = s0 + j * STEP
            if st >= L - 1:
                break
            if rng.random() < 0.18:
                continue
            m = tones[(j * 3 + k) % len(tones)]
            b0 = int(st * SR); b1 = min(N, b0 + int(2.2 * SR)); bt = t[b0:b1] - st
            f = hz(m)
            v = (np.sin(2 * np.pi * f * bt) + 0.3 * np.sin(2 * np.pi * 2.01 * f * bt)) * np.exp(-bt / 0.6) * np.clip(bt / 0.01, 0, 1)
            pan = 0.3 + 0.4 * rng.random(); g = 0.55 + 0.25 * rng.random()
            bell[b0:b1, 0] += v * g * (1 - pan); bell[b0:b1, 1] += v * g * pan
sos = butter(2, M.get("lowpass_hz", 1800), "low", fs=SR, output="sos")
pad = sosfilt(sos, pad, axis=0); bass = sosfilt(butter(2, 220, "low", fs=SR, output="sos"), bass)
mix = pad / np.abs(pad).max() * 0.55 + bell / max(1e-9, np.abs(bell).max()) * BELL + (bass / np.abs(bass).max() * 0.35)[:, None]
# simple room: exponentially decaying noise impulse
ir_t = np.arange(int(2.4 * SR)) / SR
ir = rng.standard_normal((len(ir_t), 2)) * np.exp(-ir_t / 0.55)[:, None]; ir[:, :] /= np.abs(ir).sum(0)
wet = np.stack([fftconvolve(mix[:, c], ir[:, c])[:N] for c in range(2)], 1)
out = 0.72 * mix + 0.9 * wet / np.abs(wet).max() * np.abs(mix).max() * 0.5
fade = np.ones(N); fi = int(2.5 * SR); fo = int(5.0 * SR)
fade[:fi] = np.linspace(0, 1, fi) ** 2; fade[-fo:] = np.linspace(1, 0, fo) ** 1.5
out = out * fade[:, None]; out = out / np.abs(out).max() * 0.6
wavfile.write(M["file"], SR, (out * 32767).astype(np.int16))
print("music seconds", round(L, 1), "->", M["file"])
