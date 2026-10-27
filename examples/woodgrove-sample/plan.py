# Woodgrove sample film: the timing plan. Run from the build folder: python plan.py -> plan.json
# Prototype stops (from prototype-tredence's checker): cover; ask stops once, on the approval card (beats 1-4 play
# by themselves, about 6 s of page time); close stops at b0 and b1, then shows the ask at b2; closing.
from planlib import Plan

P = Plan()
E = P.E
proto, gfx = P.proto, P.gfx


# ---------- P1: Tredence cover ----------
def cover():
    a1 = 1.0; a2 = E("A1", a1) + 0.4
    return [("A1", a1), ("A2", a2)], [], E("A2", a2) + 0.8


proto("P1", "", False, [cover])

# ---------- G1: night + simulation ----------
c1 = 0.9; tSim = 4.4; c2 = max(5.6, E("C1", c1) + 0.35); c3 = E("C2", c2) + 0.4
g1 = dict(tSim=tSim, tA0=5.4, tA1=c2 + 1.6, tH=c2 + 1.2, tS=c3 - 0.05)
g1["tI0"] = g1["tS"] + 2.5; g1["tI1"] = g1["tI0"] + 4.0
g1["end"] = max(g1["tI1"] + 1.6, E("C3", c3) + 1.0)
gfx("G1", "night", g1, [("C1", c1), ("C2", c2), ("C3", c3)])

# ---------- G2: Adele's morning ----------
e1 = 1.2; tSw = 2.8; e2 = E("E1", e1) + 0.45
g2 = dict(tSw=tSw, tLT=tSw + 0.8, tQ=e1 + 3.4, end=E("E2", e2) + 0.9)
gfx("G2", "morning", g2, [("E1", e1), ("E2", e2)])


# ---------- P2: ask through the close ----------
def ask():
    f1 = 0.8; f2 = max(6.6, E("F1", f1) + 0.35); f3 = E("F2", f2) + 0.4
    approve = f3 + 2.4                                          # as "until Adele approves" is said
    return [("F1", f1), ("F2", f2), ("F3", f3)], [approve], max(approve + 1.6, E("F3", f3) + 0.9)


def close():
    m1 = 0.6; m2 = E("M1", m1) + 0.4; m3 = E("M2", m2) + 0.45
    return [("M1", m1), ("M2", m2), ("M3", m3)], [1.6, m3 - 0.1], E("M3", m3) + 2.2


def closing():
    return [], [], 3.5


proto("P2", "#ask", True, [ask, close, closing])

P.write()
