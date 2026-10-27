# Timing plan skeleton for a Tredence concept film. new_film.py copies it to the build folder as plan.py. Rename
# the scene functions and cue ids to match the prototype's scenes and cues.json, then: python plan.py -> plan.json
# (and a printed timeline). The worked example is examples/woodgrove-sample/plan.py.
#
# A prototype-tredence demo usually runs: a Tredence frame cover -> (their world) -> product scenes on the ground
# -> the business from above (Power BI) -> the Tredence close (from -> to, what it could be worth, one ask)
# -> the #beyondpossible closing. Graphics segments sit between prototype segments where the story jumps in time
# or place (night before, the persona's morning). Delete any segment the story doesn't need.
#
# Rules of thumb:
# - A cue starts 0.35-0.45 s after the previous cue ends: E(prev, at) + 0.4. If the visual it describes
#   isn't on screen yet, start it later: max(<when the visual lands>, E(prev, at) + 0.35).
# - A -> press that reveals something lands just before the line that talks about it (cue start - 0.05),
#   or just after the line that sets it up (E(cue, at) + 0.25).
# - The first in-scene press is at least 1.4 s after the scene opens; earlier presses can be swallowed by the
#   scene crossfade.
# - Presses are only for beats that wait for the presenter. data-auto beats play by themselves: leave time for
#   them (the prototype checker's contact sheets show where each scene stops).
# - A scene ends 0.7-0.9 s after its last line; the close holds about 2 s on the ask, and the #beyondpossible
#   closing scene holds 3-4 s with no narration while the music fades.
# - Segments crossfade for 0.6 s; plan.write() asserts that no two cues overlap.
from planlib import Plan

P = Plan()
E = P.E


# ---------- P1: Tredence cover + their world (prototype opened at its first scene) ----------
def cover():
    return [("A1", 1.0)], [], E("A1", 1.0) + 0.8          # cover on screen: who it's for, fictional data stated


def world():
    b1 = 0.6; b2 = E("B1", b1) + 0.35; b3 = E("B2", b2) + 0.4
    return [("B1", b1), ("B2", b2), ("B3", b3)], [b2 - 0.05, b3 - 0.05], E("B3", b3) + 0.9


P.proto("P1", "", False, [cover, world])

# ---------- G1: night establishing shot (+ simulation when there is engine output) ----------
c1 = 0.9; tSim = 4.4; c2 = max(5.4, E("C1", c1) + 0.35); c3 = E("C2", c2) + 0.35
g1 = dict(tSim=tSim,                 # establishing shot hands over to the simulation
          tA0=5.6, tA1=c3 - 1.0,     # baseline dots stream in
          tH=c3 - 0.2,               # late rows highlighted + stat chips appear (as the "too late" line starts)
          tS=c3 + 3.0)               # search starts: shuffles, counter climbs into millions
g1["tI0"] = g1["tS"] + 2.5; g1["tI1"] = g1["tI0"] + 4.0   # optimized order, all Teal
g1["end"] = max(g1["tI1"] + 1.6, E("C3", c3) + 1.0)
P.gfx("G1", "night", g1, [("C1", c1), ("C2", c2), ("C3", c3)])
# Without simulation data, G1 is a title card on the photo:
# P.gfx("G1", "night", dict(end=E("C1", 0.9) + 1.0), [("C1", 0.9)])


# ---------- P2: the agent's overnight work (prototype opened at #overnight, replayed with r) ----------
def overnight():
    d1 = 0.7; d2 = E("D1", d1) + 0.4
    return [("D1", d1), ("D2", d2)], [], E("D2", d2) + 0.8


P.proto("P2", "#overnight", True, [overnight])

# ---------- G2: the persona's morning ----------
e1 = 1.2; tSw = 2.8; e2 = E("E1", e1) + 0.45
g2 = dict(tSw=tSw, tLT=tSw + 0.8, tQ=e1 + 3.4, end=E("E2", e2) + 0.9)
P.gfx("G2", "morning", g2, [("E1", e1), ("E2", e2)])


# ---------- P3: the Copilot scenes through the close (prototype opened at #ask) ----------
def ask():
    f1 = 0.5; send = E("F1", f1) + 0.25; f2 = send + 3.7      # send the question, line over the streamed answer
    return [("F1", f1), ("F2", f2)], [send], E("F2", f2) + 0.9


def close():
    m1 = 0.5; m2 = E("M1", m1) + 0.45                         # from -> to and the worth first, then the ask as it appears
    return [("M1", m1), ("M2", m2)], [1.6, m2 - 0.1], E("M2", m2) + 2.2


def closing():
    return [], [], 3.5                                        # #beyondpossible sign-off, no narration, music fades


# add one function per scene between ask and close (G..L cues), in the prototype's scene order
P.proto("P3", "#ask", True, [ask, close, closing])

# ---------- optional end card, when the prototype has no closing scene ----------
# P.gfx("G3", "endcard", dict(tT=0.5, tL=1.4, end=4.0), [])

P.write()
