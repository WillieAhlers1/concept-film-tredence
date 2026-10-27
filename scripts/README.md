# concept-film-tredence scripts

These scripts turn a packed prototype-tredence prototype, a voiced narration and Tredence-branded graphics into
one narrated, captioned 1080p film.  They are the Frontier concept-film pipeline (the TD Retail Credit IQ film),
with every film-specific value in one config file, `film.json`, and made to run on Windows, macOS and Linux.

## Build folder

`python <skill>/scripts/new_film.py <build> --prototype <packed.html> [--name ...] [--example woodgrove-sample]`
creates it.  Everything then runs from `<build>`:

| File | From |
|---|---|
| `*.py`, `*.js` | these scripts (refreshed every time `new_film.py` runs) |
| `graphics.html`, `fonts/`, `brand/` | the skill's template, Poppins and the Tredence logos |
| `proto/<name>.html` | the packed prototype |
| `film.json`, `plan.py`, `narration.txt` | the templates (or an example); kept on refresh unless `--force` |
| `images/`, `simdata.json` | yours: the three images and the engine's simulation data |
| `work/` | frames, segment encodes, the mix and the final MP4 (`film.json` "tmp") |

## Run order

| Step | Command | Writes | Time |
|---|---|---|---|
| 1 Check words and config | `python check_film.py` | report; exit 1 on errors | seconds |
| 2 Voice | `python voice.py` (Azure) or `--engine sapi` (scratch) | `narr.wav`, `narr.txt`, `cues.json`, `voice/` cache | ~1 s a line |
| 2b Align (one-take audio only) | `python align.py` | `cues.json` | seconds |
| 3 Plan | `python plan.py` | `plan.json`, printed timeline | seconds |
| 4 Graphics data | `python gfx_data.py` | `gfx-data.js` | seconds |
| 5 Check stills | `python stills.py` (or `node stills.js`) | `stills/st_<SEG>_<seg>_<t>.png` | ~30 s |
| 6 Film | `python record_all.py [log] [SEG ...]` (background) | `work/frames_<SEG>/` + `meta.json`, `work/rec_all.log` | ~4-5 min per film minute |
| 7 Music | `python music.py` | `music.wav` | ~10 s |
| 8 Mix | `python mix.py`, then `python mix.py --levels` | `work/<mix.file>`, `mix_fc.txt` | ~5 s |
| 9 Captions | `python subs.py` | `<captions.file>` (ASS) | seconds |
| 10 Assemble | `python assemble.py segs`, then `python assemble.py final` (background) | `work/<SEG>.mp4`, `work/<output.file>` | ~1 min + a few min |
| 11 Review | `python contact_sheet.py` | `review/sheet_NN.jpg` | ~1 min |

Re-film or re-encode only some segments: `python record_all.py work/rec.log P3`, `python assemble.py segs P3`.

## Files

| File | Does |
|---|---|
| `filmcfg.py` | Loads `./film.json` (or `$FILM_CONFIG`) over the defaults; finds ffmpeg (`film.json` "ffmpeg", `$FFMPEG`, PATH, then imageio-ffmpeg) |
| `new_film.py` | Creates or refreshes a build folder (not copied into it) |
| `check_film.py` | Tredence voice and brand check of the narration and `film.json`; lists every spoken number to trace |
| `voice.py` | Voices each line (Azure AI Speech REST, or Windows SAPI scratch), caches lines, joins with gaps, writes exact cues |
| `align.py` | For one-take audio: silencedetect + dynamic programming against expected durations to split it into cues |
| `planlib.py` | `Plan` helper: `proto()` / `gfx()` segments, `E(cue, at)`, absolute timeline, overlap assertion, `plan.json` |
| `gfx_data.py` | Writes `gfx-data.js`; stat chips take numbers from the engine totals; drops missing images (flat colour) and a missing simulation |
| `record.py` | Films one segment with Python Playwright at page-time rate 0.25 (slowtime.js + CDP Animation.setPlaybackRate) via CDP screencast; hides the prototype's presenter chrome |
| `record_all.py` | Films every segment (graphics first) and logs; ends with `ALLDONE`; falls back to `node record.js` |
| `record.js`, `stills.js` | Node Playwright fallbacks for `record.py` and `stills.py` |
| `slowtime.js` | Injected time wrapper: performance.now, Date.now, setTimeout, setInterval, requestAnimationFrame |
| `stills.py` | Stills of the graphics at `?seek=` times (`review.stills` in film.json, or every 3 s) |
| `music.py` | Original ambient score with numpy: pad chords, soft bass, bell arpeggio, room reverb, fades |
| `mix.py` | Places each cue at its time, voice loudnorm I=-16, music -14 dB with sidechain ducking, limiter 0.89; `--levels` |
| `subs.py` | ASS captions, Poppins Medium 34 on a Charcoal box, greedy chunks up to 72 characters, no short fragments |
| `assemble.py` | Per-segment CFR 30 fps encode, 0.6 s xfades, captions burned with libass (relative paths), AAC 192k, H.264 crf 19 |
| `contact_sheet.py` | Review sheets: one accurate seek every ~7 s, each frame labelled with its time and line |

## Environment notes

- Browser: `$CHR`, else `capture.chrome`, else Playwright's Chromium, else installed Edge or Chrome, else the
  sandbox's `/opt/docgen-browsers` headless shell.  `python -m playwright install chromium` if none is found.
- Node fallback: `NODE_PATH` may lack Playwright in Linux sandboxes; `record.js` falls back to
  `/usr/local/lib/node_modules/docgen-utils/node_modules`.
- ffmpeg needs libx264, aac and libass (`ffmpeg -filters` lists `subtitles`).  The imageio-ffmpeg build has them.
- libass finds Poppins in `fonts/` by its family names ("Poppins Medium"); `captions.fontsdir` is relative, which
  avoids escaping a Windows drive letter in the filter graph.  Run `assemble.py` from the build folder.
