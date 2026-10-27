---
name: concept-film-tredence
description: Tredence concept films. Turns a clickable Tredence prototype (the packed single-file HTML from prototype-tredence) and its brief into a narrated, captioned 1080p concept film for a customer meeting, with original music, data animations and graphics in the Tredence 2026 brand (Poppins, Bright Orange, official logos, #BeyondPossible), written in the Tredence voice, and iterates on it. Use when the user asks to make a video or film of a Tredence concept, prototype, storyboard or story brief; to "turn the prototype into a film"; for a "narrated walkthrough video" or "demo film" for a Tredence customer; or to change a film's narration, pacing, graphics, music, captions, voice or length. Do NOT use for slide decks (use pptx-tredence), building or fixing the prototype itself (use prototype-tredence), audio-only podcasts, a single image, or editing a video file made elsewhere.
---

# Tredence concept films

**The test that matters: would a Tredence lead play this film to the customer's business leader with a straight
face, and does the room come away saying "we could run our business differently"?**  The film carries the same
story as the prototype: the business shift, one person's everyday decision changing on the ground, the business
from above, one ask.  It looks like Tredence where Tredence speaks (cover, graphics, close) and like Microsoft
where the product works, and every number in it traces to the brief or an engine run.

What it makes: a 2:30 to 3:30 film.  One calm narrator; the prototype filmed scene by scene; short graphics
sequences in the Tredence brand (an establishing shot with an overnight simulation, the persona's morning, an
optional end card); an original ambient score; burned-in captions in Poppins.  The pipeline is the one behind the
Frontier concept films (the TD Retail Credit IQ film), rebuilt for Tredence and for Windows as well as Linux.

Sibling skills: **prototype-tredence** makes the input (the packed prototype and `brief.md`); **pptx-tredence**
is the source of the brand and voice, and makes the deck from the same brief if the user also wants slides.

## When to use

- "Make a film / video of this concept", "turn the prototype into a film", "a narrated walkthrough video"
- "A demo film like the TD one" for a Tredence customer or scenario
- Iterating on a film made this way: a line, the pacing, a graphic, the music level, captions, the voice, length

## When not to use

- Slides, a deck, a proposal: use **pptx-tredence**
- Building, fixing, restyling or repacking the prototype: use **prototype-tredence**, then come back to film it
- An audio-only brief or podcast; a single picture or poster; editing or re-cutting a video made elsewhere

## Find the skill folder

Everything ships next to this SKILL.md.  Call that folder `<skill>` (it may have a suffix such as `-2`; use the
newest).  It is read-only in some hosts: never build inside it.

```powershell
Get-ChildItem C:\ -Recurse -Filter new_film.py -ErrorAction SilentlyContinue | Where-Object FullName -match 'concept-film-tredence' | Select-Object -ExpandProperty FullName
```

```bash
find / -path '*concept-film-tredence*/scripts/new_film.py' 2>/dev/null
```

## What's in this skill

| Path | What |
|---|---|
| `scripts/` | The pipeline: `new_film.py` (build folder), `check_film.py` (voice and brand check), `voice.py` (narration), `align.py`, `plan.py` helper `planlib.py`, `gfx_data.py`, `stills.py`, `record.py` + `record_all.py` (filming), `music.py`, `mix.py`, `subs.py`, `assemble.py`, `contact_sheet.py`; Node fallbacks `record.js`, `stills.js`.  → `scripts/README.md` |
| `templates/graphics.html` | The Tredence graphics: establishing shot + simulation, the persona's morning, the end card.  Driven by `film.json`; never edited per film |
| `templates/film.json`, `plan_template.py`, `narration-script-template.txt` | Config, timing plan and narration skeletons |
| `assets/fonts/`, `assets/brand/` | Poppins (SIL OFL) and the official Tredence logos, from pptx-tredence |
| `references/` | `narration.md` (story and voice), `look.md` (graphics, images, captions), `qa-and-feedback.md` (review, feedback, delivery) |
| `examples/woodgrove-sample/` | A short worked film (fictitious Woodgrove Bank): config, plan, narration, seeded engine and a tiny test prototype |

## Inputs

1. **The packed prototype** from prototype-tredence: `working/<name>/dist/<name>.html`.  Scenes have ids
   (`#id` opens one), beats advance with →, `r` replays a scene, `h` turns click cues off.
2. **Its `brief.md`**: the design-thinking card (the business shift, who and the decision, the moment to land,
   who does what), the storyboard (one spoken line per scene), and the cast and data sheet.
3. **Engine output**, if the story has a simulation or optimisation behind its numbers.

If the prototype or brief is missing, ask once.  Without engine output, leave the simulation out (or ask whether
to build one); never invent simulated results for the film to quote.

## Environment

Python 3.10+ with `numpy`, `scipy`, `Pillow` and `playwright` (with a Chromium, or Edge/Chrome installed);
ffmpeg with libx264, aac and libass (on PATH, `$FFMPEG`, or `pip install imageio-ffmpeg`, whose build has them).
Check once: `python -c "import numpy, scipy, PIL, playwright; import filmcfg; print(filmcfg.ffmpeg())"` from a
build folder.  Node Playwright works instead of Python Playwright (`record.js`, `stills.js`).  In Copilot Cowork,
don't `pip install`: use what the sandbox has (Node Playwright under docgen-utils, ffmpeg, PodcastGenerate,
ImageGenerate).  If something is missing, say exactly what.

## The loop

Work in small, visible turns: show the narration before voicing, stills before filming, contact sheets before
delivering.  All commands run in the build folder.

0. **Build folder.**  `python <skill>/scripts/new_film.py <build> --prototype working/<name>/dist/<name>.html
   --name "<Concept> film"`.  Put `<build>` somewhere local and outside synced folders (`%TEMP%\film-<name>` on
   Windows, `/tmp/film-<name>` elsewhere): filming writes thousands of frames to `<build>/work`.  It holds the
   scripts, `graphics.html`, Poppins, the logos, the prototype in `proto/`, and `film.json`, `plan.py` and
   `narration.txt` started from the templates.  Re-running refreshes scripts and keeps your files.
1. **Read the inputs.**  From `brief.md`: the shift (from → to, the measure, its owner), the person and the
   last-mile decision, the moment to land, who does what, and every number with its source.  From the prototype:
   scene ids, and where each scene stops for a presenter press.  Run prototype-tredence's checker
   (`python <prototype-skill>/assets/check_prototype.py <packed.html>`): its contact sheets show each stop
   (`b0`, `b4`, ...); fix beat gaps there before filming.  Decide the segments: prototype runs, and graphics where
   the story jumps in time or place.
2. **Narration** (`narration.txt`, → `references/narration.md`).  25-40 lines, one idea each, 1.5-13 s spoken,
   in the Tredence voice.  The first line says it's a concept from Tredence and that the company, people and numbers
   are fictional; the close says how the business could work, what it could be worth (illustrative), and one ask.
   Give each line a cue id (A1, B1, B2 ... by scene) in `film.json` `narration.cue_ids`.  Run
   `python check_film.py`, fix every error, and check its table of spoken numbers against the brief.  Show the
   script to the user before voicing.
3. **Voice.**  `python voice.py` voices each line with an Azure AI Speech neural voice (`SPEECH_KEY` and
   `SPEECH_REGION`; default `en-US-AndrewMultilingualNeural`), joins them with 0.6 s gaps and writes `narr.wav`,
   `narr.txt` and `cues.json` with exact boundaries.  Lines are cached, so an edited line is the only one re-voiced.
   No key yet: `python voice.py --engine sapi` makes a Windows scratch track for timing and filming drafts, never
   for delivery.  In Copilot Cowork: voice all lines in one `PodcastGenerate` call (`format="single_host"`,
   `voice_host="en-US-AndrewMultilingualNeural"`, one host turn per line), save the audio and transcript as
   `narr.mp3` / `narr.txt`, set `narration.audio` to `narr.mp3`, and run `python align.py`; check its printed
   durations against the expected ones (a pause inside a line as long as the gap between lines can move a split).
4. **Images** (→ `references/look.md` §Images).  Three 16:9 photographs: the workplace at night, the person
   arriving, the person at work.  Use the host's image generator (ImageGenerate in Cowork, Azure OpenAI image
   models, or what the user provides), fictional people only, no logos, no text, open space on the left for a
   title.  Save as `images/night.jpg`, `images/arrival.jpg`, `images/desk.jpg`.  Without an image generator the
   graphics fall back to flat Tredence colour; say so in your reply.
5. **Graphics** (`film.json` `graphics`).  Kicker, title (`*key phrase*` turns Bright Orange), simulation labels,
   stat chips (numbers as format fields against the engine totals, so they are never typed), the morning clock,
   name card, work-list card, end card.  Simulation data: `simdata.json` straight from the engine
   (`examples/woodgrove-sample/make_simdata.py` shows the shape).  `python gfx_data.py`, then `python plan.py`
   (step 6) and `python stills.py`: look at every still.  Text fits, numbers right, the bottom ~190 px clear for
   captions, nothing off-palette.
6. **Timing plan** (`plan.py`).  Segments alternate prototype and graphics.  Place each cue against the visual it
   describes (0.35-0.45 s after the previous cue ends, or later if the visual isn't there yet); place → presses
   relative to the cues, only for beats that wait for the presenter; let `data-auto` beats play.  End on the
   close's ask (~2 s hold) and 3-4 s of the #beyondpossible closing scene, or the end card.  `python plan.py`
   asserts no overlaps and prints the timeline.  Aim for 2:30-3:30.
7. **Film.**  `python record_all.py` as a background job (`<build>/work/rec_all.log` ends with `ALLDONE`).  Each
   segment runs in headless Chromium at 1920 × 1080 with page time at a quarter speed, captured by CDP screencast.
   Prototype segments wait 30 s for the engine warm-up, hide the presenter chrome (Back/Next buttons, the Next
   pill, scene dots), press `h`, press `r` when opened at `#scene`, then press → on schedule.  About 4-5 minutes
   of filming per minute of film.  Re-film one segment: `python record_all.py <log> P3`.
8. **Music.**  `python music.py`: an original ambient score generated here (pads, soft bass, light bells).
   Never imitate a named artist or use a licensed or downloaded track.
9. **Mix.**  `python mix.py`, then `python mix.py --levels`: voice about -18 dB mean; music alone about -27 to
   -31 dB.
10. **Captions.**  `python subs.py`: Poppins Medium 34 on a Charcoal box, sitting above the Tredence frame footer.
11. **Assemble.**  `python assemble.py segs`, then `python assemble.py final` (background; a few minutes):
    0.6 s crossfades, captions burned in, AAC 192k, H.264 crf 19 → `<build>/work/<output.file>`.
12. **Review and deliver** (→ `references/qa-and-feedback.md`).  `python contact_sheet.py` → `review/sheet_NN.jpg`,
    a frame every ~7 s labelled with its time and line.  View every sheet: each frame against its line, the beat
    state, captions clear of key UI, no presenter chrome, no missing builds, Tredence look on graphics.  Fix and
    re-run the affected steps.  Then copy into the user's workspace, next to the prototype:
    `working/<name>/film/<Customer-or-Concept>-<Concept>-Film-v<N>.mp4`, and the source (`film.json`, `plan.py`,
    `narration.txt`, `cues.json`, `simdata.json`, `images/`, a short README) to `working/<name>/film/source-v<N>/`.
    Delete `<build>/work` once the user is happy.

## Your reply

Short, plain language, no script or tool names:
- **Film**: file, length (m:ss), size
- **Scene timeline**: a table of start time → what's on screen (from the plan's printed timeline)
- **What changed** since the last draft (first draft: what the film covers, and the business shift in one line)
- **What's illustrative**, and its basis
- **What couldn't be checked**: the audio can't be listened to here (give the measured levels); a scratch voice
  if one was used; images if they fell back to flat colour
- **Next options**: 2-4 specific changes from the levers below

## Iteration levers

| Change | Edit | Re-run |
|---|---|---|
| A narration line | the line in `narration.txt` | check_film, voice (only that line re-voices), plan, re-film segments whose press times moved, mix, captions, assemble |
| Pacing | gaps and press times in `plan.py` | plan, re-film affected segments, mix, captions, `assemble.py segs <SEG>`, final |
| Graphics text or phases | `graphics` in `film.json`, or params in `plan.py` (tSim tA0 tA1 tH tS tI0 tI1, tSw tLT tQ, tT tL) | gfx_data, stills, re-film G segments, assemble |
| Music level or mood | `mix.music_db`; `music.seed`, `chords`, `bass`, `bell_gain`, `lowpass_hz` | music, mix, assemble final |
| Captions off | `captions.enabled: false` | assemble final |
| Captions in a band below the picture | scale the picture to leave a ~160 px band (assemble change) and raise `captions.margin_v` into it | captions, assemble final |
| Voice | `voice.name` (any Azure neural voice) or `voice.rate` | voice, plan, mix, captions, assemble |
| Length | target 2:30-3:30; trim lines first, then scenes that repeat a point | plan, re-film, mix, captions, assemble |
| Cold open | a `night` segment first, with no simulation (`tSim` past `end`) and one line | gfx_data, plan, film, all audio, assemble |
| End card | `P.gfx("G3", "endcard", dict(tT=0.5, tL=1.4, end=4.0), [])` last in `plan.py`, when the prototype has no closing scene | as cold open |

## Gotchas

- **Presenter chrome.**  prototype-tredence's kit always shows Back/Next buttons (at 72% opacity) and a Next pill.
  The recorder hides them with `prototype.film_css`; never edit the kit, and never film the prototype another way.
- `slowtime.js`'s requestAnimationFrame wrapper must call `cb(performance.now())`; passing rAF's own timestamp
  stalls text streaming once Animation.setPlaybackRate is set.
- **Beat gaps.**  A scene with a gap in its beat numbers silently waits for an extra → and shifts every later press.
  Run the prototype checker first; each scene must stop only where a presenter click is intended.
- A → less than ~1 s after entering a scene can be swallowed by the crossfade: first in-scene press ≥ 1.4 s.
- **One-take alignment.**  `align.py` splits at the longest pauses that fit the expected durations.  A voice that
  pauses after a short sentence ("Tuesday morning.") for as long as between lines can move a split by seconds.
  Prefer `voice.py` (exact boundaries); after `align.py`, compare its printed durations with the expected ones.
- **Captions and the frame footer.**  `captions.margin_v` 80 keeps the footer (copyright, concept label, page
  number, T) visible on Tredence frame scenes; a lower value covers it.
- **Key phrase on orange.**  The end card's title is all white, as the template's divider; `*key phrase*` only
  turns orange on dark or photo backgrounds.
- Keep counters (`data-count`) out of wrapping text in the prototype: a changing width breaks the layout.
- Run long jobs (filming, the final encode) in the background, from a local build folder.  A synced folder
  (OneDrive) or a workspace mount can stall or drop mid-run; in Linux sandboxes `/tmp` can be wiped between turns:
  re-copy the prototype before filming.
- ffprobe and drawtext may be missing: the scripts only use `ffmpeg -i` and libass.
- Pull review frames with one accurate seek per time (as `contact_sheet.py` does); an fps filter drifts from the
  labels.

## Non-negotiables

- **Fictitious and labelled.**  The company, people and numbers are fictional; say so once at the start, keep the
  prototype's concept label on screen, and the graphics carry it too.  The customer you present to is named only
  if the user confirmed it's allowed; inside the story the company stays fictitious.
- **Every number traces** to the brief's data sheet or the engine output, rounded truthfully for the ear.  Impact
  is called illustrative.  If a number has no source, leave it out and tell the user.  Time freed is capacity for
  more or better work, never a cut in staff.
- **The Tredence voice** (`references/narration.md`): start in the customer's world, the last mile, "we" and "you",
  calm and specific, never promotional.  "Tredence", never "TREDENCE".  `check_film.py` blocks the banned words.
- **The Tredence brand on graphics** (`references/look.md`): Poppins only, the closed palette, flat colour, official
  logos unrecoloured.  Microsoft product scenes stay Microsoft: no Tredence styling inside them.
- **No promises.**  No product names, prices, dates or capabilities beyond what the prototype shows; preview
  features stay labelled as the prototype labels them.
- **Images and music are made here.**  AI images show fictional people only, no logos, no text, never a real person
  without consent.  Music is generated, never imitated or licensed.
- **Keep every draft.**  New drafts get a new version number; never overwrite an earlier MP4 or source folder.
- **Never claim the audio was listened to**; report the measured levels.  Never deliver a scratch voice as final.
- If a step fails (cue count mismatch, missing frames, encode error), fix it or say what's missing; never deliver
  a film with known gaps without saying so.

## Human authority

You draft, build and check.  The user owns the story, the claims and the decision to show or send the film.  Never
present the concept as a working product, share it externally, or claim approval that wasn't given.  The Tredence
voice guide is a draft pending review by a Tredence brand or communications owner.

Built on the `concept-film` (Frontier) skill's pipeline, the `prototype-tredence` skill (input, engine, story
method) and the `pptx-tredence` skill (Tredence 2026 brand, logos, Poppins and voice).
