"""Checks a concept film's words and config against the Tredence voice and brand before voicing and filming.

Usage: python check_film.py [narration.txt]     (run from the build folder; exits 1 when it finds an error)

Narration: Tredence voice banned words (the same list as prototype-tredence's checker), "TREDENCE" in capitals,
exclamation marks, emoji, the fictional-data line at the start, an ask at the end, line lengths, staff-cut framing,
and a table of every number spoken, to trace each one to the brief or the engine output.
film.json: leftover <placeholders>, banned words in on-screen text, titles opening with a number, colours outside
the Tredence palette, the prototype, images, simulation data and Poppins present, cue ids matching the script.
"""
import json
import os
import re
import sys

from filmcfg import load

TELLS = [r"\blorem\b", r"\bipsum\b", r"\bacme\b", r"\bjohn doe\b", r"\bjane doe\b", r"\bplaceholder\b", r"\bTODO\b",
         r"\bunlock\w*\b", r"\bleverag\w+\b", r"\bseamless\w*\b", r"\bsupercharg\w+\b", r"\brevolutioni\w+\b",
         r"\bgame[- ]chang\w+\b", r"\bdelve\b", r"\bsynerg\w+\b", r"\bempower\w*\b", r"\bcutting[- ]edge\b",
         r"\bnext[- ]gen\w*\b", r"\b(?:Microsoft|M) ?365 Copilot\b", r"\bharness\w*\b", r"\bjourney\b", r"\bin today's\b",
         r"\bmagic\w*\b", r"\b99\.9+%", r"\bwhat you(?: just)? saw\b", r"\bsingle pane of glass\b", r"\bone[- ]stop[- ]shop\b",
         r"\bflywheel\w*\b", r"\bunleash\w*\b", r"\butili[sz]\w+\b", r"\bideat\w+\b", r"\boperationali[sz]\w+\b",
         r"\bbest[- ]in[- ]class\b", r"\bworld[- ]class\b", r"\bexcited to\b", r"\bTredence (?:Inc|Analytics)\b",
         r"\benable your organi[sz]ation\b"]
STAFF = r"\b(?:headcount|head count|FTEs?|layoffs?|fewer (?:people|staff|employees)|cut (?:staff|jobs)|replace (?:people|staff))\b"
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF]")
PALETTE = {"#fe5000", "#6dcdb8", "#004e42", "#8a1f04", "#f48120", "#404041", "#929497", "#e6e7e8", "#ffffff",
           "#000000", "#ffede5", "#e2f5f1", "#fff", "#000"}
NUM = re.compile(r"\$?\d+(?:[,.:]\d+)*(?:\s?(?:%|percent|million|billion|thousand)\b)?")
_W = (r"two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|"
      r"eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|billion|"
      r"half|quarter|third|dozen")
WORDNUM = re.compile(rf"\b(?:{_W})s?(?:[\s-]+(?:{_W})s?)*\b", re.I)

errors, warns = [], []


def tells(text, where):
    for p in TELLS:
        m = re.search(p, text, re.I)
        if m:
            errors.append(f"{where}: '{m.group(0)}' is off-voice for Tredence (see references/narration.md, Words)")
    if "TREDENCE" in text:
        errors.append(f"{where}: write 'Tredence', never 'TREDENCE' (that is the logo)")
    if "!" in text:
        errors.append(f"{where}: no exclamation marks in the Tredence voice")
    if EMOJI.search(text):
        errors.append(f"{where}: emoji")


def walk(v, path=""):
    if isinstance(v, dict):
        for k, x in v.items():
            yield from walk(x, f"{path}.{k}" if path else k)
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from walk(x, f"{path}[{i}]")
    else:
        yield path, v


def main():
    cfg = load(); NC = cfg["narration"]
    script = sys.argv[1] if len(sys.argv) > 1 else NC.get("script", "narration.txt")
    pre = NC["prefix"].strip()
    lines = [s.strip()[len(pre):].strip() for s in open(script, encoding="utf-8") if s.strip().startswith(pre)] \
        if os.path.exists(script) else []
    if not lines:
        errors.append(f"{script}: no '{pre}' lines found")
    ids = NC["cue_ids"] or [f"C{k + 1:02d}" for k in range(len(lines))]
    if lines and len(ids) != len(lines):
        errors.append(f"{len(lines)} narration lines but {len(ids)} cue ids in film.json narration.cue_ids")
    if lines and not 25 <= len(lines) <= 40:
        warns.append(f"{len(lines)} lines: a 2:30-3:30 film usually has 25-40 (fine for a short cut or a test)")
    total = 0.0; nums = []
    for cid, t in zip(ids, lines):
        where = f"narration {cid}"
        tells(t, where)
        if re.search(r"<[^>]+>", t):
            errors.append(f"{where}: template placeholder left: {re.search(r'<[^>]+>', t).group(0)}")
        if re.search(STAFF, t, re.I):
            errors.append(f"{where}: time freed is capacity for more or better work, never a cut in staff")
        est = len(t) / 15.0; total += est + 0.5
        if est < 1.5 or est > 13:
            warns.append(f"{where}: about {est:.1f} s spoken; keep lines 1.5-13 s (one idea each)")
        digits = list(NUM.finditer(t)); spans = [m.span() for m in digits]
        words = [m for m in WORDNUM.finditer(t) if not any(a <= m.start() < b for a, b in spans)]
        found = [m.group(0).strip() for m in sorted(digits + words, key=lambda m: m.start())]
        if found:
            nums.append((cid, ", ".join(found)))
    if lines:
        if not re.search(r"\bfictio\w+|\billustrative\b|\bnot real\b", lines[0], re.I):
            errors.append("narration: say in the first line that the customers, people and numbers are fictional")
        if not re.search(r"\bask\b|next step|\bpropose\b|\bsuggest\b|\blet's\b|\bwe'd start\b|\bwe would start\b",
                         " ".join(lines[-2:]), re.I):
            warns.append("narration: end on one ask (a specific, small next step), spoken as it appears on screen")
        if not any("Tredence" in x for x in lines):
            warns.append("narration: say once who the concept is from ('a concept from Tredence for ...')")
        print(f"narration: {len(lines)} lines, about {total / 60:.1f} min spoken (estimate)")
    if nums:
        print("numbers spoken (trace each one to the brief's data sheet or the engine output; round them truthfully):")
        for cid, n in nums:
            print(f"  {cid:>4}  {n}")

    raw = json.load(open(os.environ.get("FILM_CONFIG", "film.json"), encoding="utf-8")) if os.path.exists(
        os.environ.get("FILM_CONFIG", "film.json")) else {}
    if not raw:
        errors.append("film.json not found (run new_film.py)")
    for path, v in walk(raw):
        if not isinstance(v, str):
            continue
        if re.search(r"<[A-Z][^>]*>", v):
            errors.append(f"film.json {path}: placeholder left: {v}")
        if path.startswith("graphics.") and not path.endswith(("file", "simdata")) and "images" not in path:
            tells(v, f"film.json {path}")
            if re.fullmatch(r"#[0-9a-fA-F]{3,6}", v) and v.lower() not in PALETTE:
                errors.append(f"film.json {path}: {v} is outside the Tredence palette")
    for key in ("night.title", "morning.name"):
        a, b = key.split(".")
        v = ((raw.get("graphics") or {}).get(a) or {}).get(b, "")
        if a == "night" and re.match(r"\s*\d", v or ""):
            errors.append(f"film.json graphics.{key}: never open a title with a number or a count")
    G = cfg["graphics"]
    proto = os.path.join(cfg["prototype"]["dir"], cfg["prototype"]["file"])
    if not os.path.exists(proto):
        errors.append(f"prototype not found: {proto} (the packed file from prototype-tredence's pack step)")
    for k, p in (G.get("images") or {}).items():
        if not os.path.exists(p):
            warns.append(f"image '{k}' missing ({p}): its graphics fall back to flat Tredence colour")
    if "sim" in G and not os.path.exists(G.get("simdata") or ""):
        warns.append("graphics.sim is set but simdata.json is missing: the simulation sequence will be left out")
    fd = cfg["captions"]["fontsdir"]
    if not os.path.exists(os.path.join(fd, "Poppins-Medium.ttf")):
        errors.append(f"Poppins missing in {fd}/ (copied by new_film.py from the skill's assets/fonts)")
    if os.path.exists(cfg["cues"]):
        C = json.load(open(cfg["cues"], encoding="utf-8"))
        if list(C) != list(ids):
            errors.append("cues.json ids differ from film.json narration.cue_ids: re-run voice.py (or align.py)")
        elif lines and [C[i]["text"] for i in ids] != lines:
            warns.append("cues.json text differs from the script: re-run voice.py so the film says what the script says")
    if os.path.exists(cfg["plan"]):
        tot = json.load(open(cfg["plan"], encoding="utf-8"))["total"]
        if not 150 <= tot <= 225:
            warns.append(f"plan length {int(tot // 60)}:{tot % 60:04.1f}: aim for 2:30-3:30 (fine for a test cut)")

    for w in warns:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"{len(errors)} error(s), {len(warns)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
