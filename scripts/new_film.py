"""Creates (or refreshes) a film build folder from this skill.

Usage: python <skill>/scripts/new_film.py <build_dir> --prototype <packed.html> [--name "Woodgrove lending film"]
                                                    [--example woodgrove-sample] [--force]

Copies the pipeline scripts, graphics.html, Poppins and the Tredence logos into <build_dir>, the packed prototype
into <build_dir>/proto/, and starts film.json, plan.py and narration.txt from the templates (or from an example).
Scripts, graphics, fonts and logos are always refreshed; film.json, plan.py and narration.txt are kept unless
--force. Frames and encodes go to <build_dir>/work (film.json "tmp").
Put the build folder somewhere local and writable, outside a synced folder (OneDrive), for example
%TEMP%\\film-<short> on Windows or /tmp/film-<short> elsewhere: filming writes thousands of frames.
"""
import argparse
import json
import os
import shutil
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("build_dir")
    ap.add_argument("--prototype", help="packed prototype HTML (prototype-tredence: working/<name>/dist/<name>.html)")
    ap.add_argument("--name", help="film name for film.json")
    ap.add_argument("--example", help="start from examples/<name> instead of the templates")
    ap.add_argument("--force", action="store_true", help="overwrite film.json, plan.py and narration.txt")
    a = ap.parse_args()
    B = Path(a.build_dir).resolve(); B.mkdir(parents=True, exist_ok=True)
    for f in (SKILL / "scripts").iterdir():
        if f.suffix in (".py", ".js") and f.name != "new_film.py":
            shutil.copy2(f, B / f.name)
    shutil.copy2(SKILL / "templates" / "graphics.html", B / "graphics.html")
    for sub in ("fonts", "brand"):
        shutil.copytree(SKILL / "assets" / sub, B / sub, dirs_exist_ok=True)
    (B / "images").mkdir(exist_ok=True)
    src = {"film.json": SKILL / "templates" / "film.json",
           "plan.py": SKILL / "templates" / "plan_template.py",
           "narration.txt": SKILL / "templates" / "narration-script-template.txt"}
    if a.example:
        ex = SKILL / "examples" / a.example
        assert ex.is_dir(), f"no example {a.example} in {SKILL / 'examples'}"
        for f in ex.iterdir():
            if f.is_file() and f.name not in src and f.suffix != ".md":
                shutil.copy2(f, B / f.name)
        if (ex / "images").is_dir():
            shutil.copytree(ex / "images", B / "images", dirs_exist_ok=True)
        src.update({k: ex / k for k in src if (ex / k).exists()})
    for name, s in src.items():
        if a.force or not (B / name).exists():
            shutil.copy2(s, B / name); print("new", name)
        else:
            print("kept", name)
    cfg = json.load(open(B / "film.json", encoding="utf-8"))
    if a.prototype:
        p = Path(a.prototype).resolve()
        assert p.exists(), f"prototype not found: {p}"
        (B / "proto").mkdir(exist_ok=True)
        shutil.copy2(p, B / "proto" / p.name)
        cfg.setdefault("prototype", {}).update({"dir": "proto", "file": p.name})
    if a.name:
        cfg["name"] = a.name
    cfg["tmp"] = cfg.get("tmp") or "work"
    json.dump(cfg, open(B / "film.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("build folder ready:", B)
    print("next: write narration.txt, then  python check_film.py  (run every script from this folder)")


if __name__ == "__main__":
    main()
