# Woodgrove sample: a small seeded queue model that stands in for a customer's engine, and writes simdata.json for
# graphics.html. Every number the sample film shows or says comes from this run (seed 2710); nothing is typed.
# Nine small-business loan applications, one credit analyst, one working day (8 AM to 5 PM, a lunch break);
# work that runs past 5 PM spills into tomorrow. Each simulated day draws every file's work time at random.
# Baseline = arrival order. The search tries random orders plus earliest-deadline-first and keeps the best.
# Usage: python make_simdata.py [simdata.json]
import json
import sys

import numpy as np

SEED = 2710; DAYS = 2000; KEEP = 260; ORDERS = 1500
FILES = [  # name, product, deadline hour (24 = tomorrow 0:00, 99 = none), amount, mean work hours
    ("Fabrikam Studio", "Equipment loan", 99, 85000, 1.1),
    ("Coho Winery", "Working capital line", 33.5, 240000, 1.3),
    ("Proseware Print", "Line increase", 99, 60000, 0.8),
    ("Northwind Traders", "Equipment loan", 11.5, 310000, 1.0),
    ("Litware Labs", "Term loan", 99, 150000, 1.2),
    ("Fourth Coffee", "Rate-hold refinance", 14.5, 195000, 0.9),
    ("Wingtip Toys", "Seasonal line", 33.0, 120000, 0.9),
    ("Alpine Ski House", "Seasonal line", 16.0, 275000, 1.0),
    ("Tailspin Toys", "Term loan", 99, 90000, 0.7),
]
N = len(FILES)
rng = np.random.default_rng(SEED)
work = np.array([f[4] for f in FILES])[None, :] * rng.lognormal(0, 0.35, size=(DAYS, N))
dl = np.array([f[2] for f in FILES], dtype=float); amt = np.array([f[3] for f in FILES], dtype=float)
has_dl = dl < 90


def simulate(order):
    t = np.full(DAYS, 8.0); out = np.zeros((DAYS, N))
    for i in order:
        d = work[:, i].copy()
        d += np.where((t < 12.5) & (t + d > 12.5), 0.5, 0.0)   # lunch
        t = t + d
        out[:, i] = np.where(t > 17, 32 + (t - 17), t)         # past 5 PM: tomorrow from 8 AM
    return out


def score(order):
    D = simulate(order); on = (D <= dl[None, :]) | ~has_dl[None, :]
    ev = (amt[None, :] * np.where(on, 0.9, 0.6)).sum(1).mean() / 1e6
    return dict(ontime_files=round(float(((D <= dl[None, :]) & has_dl[None, :]).sum(1).mean()), 2),
                ev_m=round(float(ev), 2)), D


fifo = list(range(N))
best = sorted(range(N), key=lambda i: dl[i]); tried = 1
bs, _ = score(best)
for _ in range(ORDERS - 1):
    o = list(rng.permutation(N)); s, _ = score(o); tried += 1
    if (s["ontime_files"], s["ev_m"]) > (bs["ontime_files"], bs["ev_m"]):
        best, bs = o, s
today, A = score(fifo); _, Dm = score(best)
rows = [dict(id=f"WB-{4100 + i}", name=f[0], product=f[1], dl=float(f[2]), amt=f[3],
             A=[round(float(v), 3) for v in A[:KEEP, i]], D=[round(float(v), 3) for v in Dm[:KEEP, i]])
        for i, f in enumerate(FILES)]
out = dict(rows=rows, fifo=fifo, iq=[int(i) for i in best], futures=tried * DAYS, orders_tried=tried,
           deadline_files=int(has_dl.sum()), totals=dict(today_order=today, iq_order=bs))
json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else "simdata.json", "w", encoding="utf-8"))
print("deadline files", out["deadline_files"], "| orders tried", tried, "| simulated days", out["futures"])
print("arrival order:", today, "| best order:", bs, "| order:", [FILES[i][0] for i in best])
for i, f in enumerate(FILES):
    if has_dl[i]:
        print(f"  {f[0]:<18} on time {np.mean(A[:, i] <= dl[i]):.0%} arrival -> {np.mean(Dm[:, i] <= dl[i]):.0%} best")
