"""Voices the narration one line at a time and writes narr.wav, narr.txt and cues.json with exact boundaries.

Usage: python voice.py [narration.txt] [--engine azure|sapi] [--voice NAME]

- Reads the "Host: " lines of the narration script (lines starting with # are comments). One line = one cue; the
  ids come from film.json narration.cue_ids (or C01, C02, ...).
- azure (default, for anything a customer hears): Azure AI Speech neural voice through the REST API. Needs
  SPEECH_KEY and SPEECH_REGION (or AZURE_SPEECH_KEY / AZURE_SPEECH_REGION; SPEECH_ENDPOINT overrides the region URL).
- sapi: the Windows built-in voice. A scratch track for timing and filming drafts only; never deliver it.
- Each line is cached in voice/ by engine, voice, rate and text, so after editing one line only that line is
  re-voiced. Lines are trimmed of edge silence and joined with narration.gap_s of silence.
When the narration was voiced in one take elsewhere (PodcastGenerate in Copilot Cowork, a studio recording), skip
this script: save the audio and its "Host: " transcript as narration.audio / narration.transcript and run align.py.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import wave
from xml.sax.saxutils import escape

import numpy as np

from filmcfg import load

SR = 48000


def read_lines(path, prefix):
    out = []
    for raw in open(path, encoding="utf-8"):
        s = raw.strip()
        if s.startswith(prefix.strip()):
            out.append(s[len(prefix.strip()):].strip())
    return out


def azure(text, voice, rate, dest):
    key = os.environ.get("SPEECH_KEY") or os.environ.get("AZURE_SPEECH_KEY")
    region = os.environ.get("SPEECH_REGION") or os.environ.get("AZURE_SPEECH_REGION")
    url = os.environ.get("SPEECH_ENDPOINT") or (region and f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1")
    if not (key and url):
        raise SystemExit("Azure AI Speech needs SPEECH_KEY and SPEECH_REGION (or SPEECH_ENDPOINT). "
                         "For a timing draft on Windows, use --engine sapi.")
    lang = "-".join(voice.split("-")[:2])
    ssml = (f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{lang}'>"
            f"<voice name='{voice}'><prosody rate='{rate}'>{escape(text)}</prosody></voice></speak>")
    req = urllib.request.Request(url, data=ssml.encode("utf-8"), method="POST", headers={
        "Ocp-Apim-Subscription-Key": key, "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "riff-48khz-16bit-mono-pcm", "User-Agent": "concept-film-tredence"})
    with urllib.request.urlopen(req, timeout=60) as r:
        open(dest, "wb").write(r.read())


def sapi(text, rate, dest):
    if sys.platform != "win32":
        raise SystemExit("the sapi engine is Windows only; use --engine azure")
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(text); src = f.name
    ps = ("Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
          f"$s.Rate = {int(rate)}; "
          "$fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(48000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono); "
          f"$s.SetOutputToWaveFile('{dest}', $fmt); $s.Speak([IO.File]::ReadAllText('{src}')); $s.Dispose()")
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, capture_output=True)
    finally:
        os.unlink(src)


def read_wav(path):
    with wave.open(path) as w:
        assert w.getsampwidth() == 2, f"{path}: expected 16-bit PCM"
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
        if w.getnchannels() > 1:
            a = a.reshape(-1, w.getnchannels()).mean(1)
        sr = w.getframerate()
    if sr != SR:   # simple linear resample; both engines are asked for 48 kHz, so this is rarely used
        a = np.interp(np.linspace(0, len(a) - 1, int(len(a) * SR / sr)), np.arange(len(a)), a)
    return a


def trim(a, db=-45.0, pad_s=0.04):
    thr = 32767 * 10 ** (db / 20); idx = np.flatnonzero(np.abs(a) > thr)
    if not len(idx):
        return a
    p = int(pad_s * SR)
    return a[max(0, idx[0] - p): min(len(a), idx[-1] + p)]


def main():
    cfg = load(); NC = cfg["narration"]; V = cfg["voice"]
    ap = argparse.ArgumentParser()
    ap.add_argument("script", nargs="?", default=NC.get("script", "narration.txt"))
    ap.add_argument("--engine", default=V["engine"], choices=["azure", "sapi"])
    ap.add_argument("--voice", default=V["name"])
    a = ap.parse_args()
    lines = read_lines(a.script, NC["prefix"])
    ids = NC["cue_ids"] or [f"C{k + 1:02d}" for k in range(len(lines))]
    assert lines, f"no '{NC['prefix'].strip()}' lines in {a.script}"
    assert len(ids) == len(lines), f"{len(lines)} narration lines but {len(ids)} cue ids in film.json"
    os.makedirs("voice", exist_ok=True)
    gap = np.zeros(int(NC["gap_s"] * SR), dtype=np.float32)
    parts = []; cues = {}; t = 0.0
    for cid, text in zip(ids, lines):
        rate = V["rate"] if a.engine == "azure" else V["sapi_rate"]
        h = hashlib.sha1(f"{a.engine}|{a.voice}|{rate}|{text}".encode()).hexdigest()[:12]
        f = os.path.abspath(os.path.join("voice", f"{cid}-{h}.wav"))
        if not os.path.exists(f):
            print("voicing", cid, text[:60], flush=True)
            azure(text, a.voice, rate, f) if a.engine == "azure" else sapi(text, rate, f)
        x = trim(read_wav(f))
        if parts:
            parts.append(gap); t += len(gap) / SR
        d = len(x) / SR
        cues[cid] = {"src": [round(t, 3), round(t + d, 3)], "dur": round(d, 3), "text": text}
        parts.append(x); t += d
    audio = np.concatenate(parts); peak = np.abs(audio).max()
    if peak > 32767 * 0.9:
        audio = audio * (32767 * 0.9 / peak)
    audio = np.clip(audio, -32768, 32767).astype(np.int16)
    with wave.open(NC["audio"], "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(audio.tobytes())
    with open(NC["transcript"], "w", encoding="utf-8") as fo:
        fo.write("".join(f"{NC['prefix']}{x}\n" for x in lines))
    json.dump(cues, open(cfg["cues"], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    if a.engine == "sapi":
        print("SCRATCH VOICE (Windows SAPI): for timing drafts only. Re-voice with --engine azure before delivery.")
    print(f"{len(lines)} lines, {t:.1f} s ->", NC["audio"], NC["transcript"], cfg["cues"])
    for cid in ids:
        print(f"  {cid} {cues[cid]['dur']:5.2f}s  {cues[cid]['text'][:70]}")


if __name__ == "__main__":
    main()
