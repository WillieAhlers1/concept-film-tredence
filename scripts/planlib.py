"""Helpers for a film's timing plan.

A film's plan script (templates/plan_template.py, or examples/woodgrove-sample/plan.py) creates a Plan,
describes its segments, and calls write(). Segments alternate prototype ("proto") and graphics ("gfx").

- proto(name, hash, replay, scenes): one browser session on the packed prototype opened at `hash`
  ("" = first scene, "#overnight" = that scene). Each scene is a function returning
  (cues, presses, duration): cues = [(cue_id, seconds from scene start)], presses = in-scene → presses
  (seconds from scene start). The → that moves to the next scene is added automatically at the scene boundary.
- gfx(name, seg, params, cues): one graphics.html sequence (`?seg=`), timed by params; params["end"] is its length.
- write(): builds the absolute timeline (segments overlap by the crossfade), asserts no two cues overlap and
  every cue is placed (require_all=False for a partial test plan), writes plan.json and prints the timeline.
"""
import json

from filmcfg import load


class Plan:
    def __init__(self, cfg=None):
        self.cfg = cfg or load()
        self.C = json.load(open(self.cfg["cues"], encoding="utf-8"))
        self.D = {k: v["dur"] for k, v in self.C.items()}
        self.X = self.cfg["crossfade_s"]
        self.segs = []

    def E(self, c, s):
        """End time of cue c when it starts at s."""
        return s + self.D[c]

    def proto(self, name, hash, replay, scenes):
        t = 0.0; presses = []; cues = []; marks = []
        for k, sc in enumerate(scenes):
            if k > 0:
                presses.append(round(t, 3))
            marks.append([sc.__name__, round(t, 3)])
            loc_c, loc_p, dur = sc()
            cues += [(c, round(t + s, 3)) for c, s in loc_c]
            presses += [round(t + p, 3) for p in loc_p]
            t += dur
        self.segs.append(dict(name=name, kind="proto", hash=hash, replay=replay, dur=round(t, 3),
                              presses=presses, cues=cues, scenes=marks))

    def gfx(self, name, seg, params, cues, dur=None):
        dur = params["end"] if dur is None else dur
        self.segs.append(dict(name=name, kind="gfx", seg=seg, params={k: round(v, 3) for k, v in params.items()},
                              dur=round(dur, 3), cues=cues))

    def write(self, min_gap=0.2, require_all=True):
        X = self.X; t = 0.0; allc = []
        for k, s in enumerate(self.segs):
            s["start"] = round(t, 3)
            allc += [dict(id=c, at=round(t + o, 3), src=self.C[c]["src"], text=self.C[c]["text"]) for c, o in s["cues"]]
            t += s["dur"] - (X if k < len(self.segs) - 1 else 0)
        total = round(t, 3)
        allc.sort(key=lambda c: c["at"])
        for a, b in zip(allc, allc[1:]):
            assert a["at"] + self.D[a["id"]] + min_gap <= b["at"], f"cue {a['id']} runs into {b['id']}"
        unused = sorted(set(self.C) - {c["id"] for c in allc})
        assert not (require_all and unused), f"cues never placed: {unused}"
        json.dump(dict(total=total, X=X, segments=self.segs, cues=allc), open(self.cfg["plan"], "w", encoding="utf-8"),
                  indent=1, ensure_ascii=False)
        print("total", total, f"({int(total // 60)}:{total % 60:04.1f})")
        for s in self.segs:
            print(s["name"], s["start"], s["dur"], s.get("params", ""), len(s.get("presses", [])))
        print("timeline:")
        for s in self.segs:
            for nm, off in (s.get("scenes") or [[s.get("seg", s["name"]), 0.0]]):
                a = s["start"] + off
                print(f"  {int(a // 60)}:{a % 60:04.1f}  {s['name']} {nm}")
        return total
