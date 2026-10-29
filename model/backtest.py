"""Backtest: replay a count in simulated station orders and score the projection.

IMPORTANT: real arrival orders for past elections are not public, so orders are SIMULATED.
Orders that correlate with politics (small stations first, low turnout first, low-Likud first)
are deliberately unfavourable to the naive "counted so far" baseline.
"""
import json, os, sys, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
from .load import load_history, load_live, live_snapshots, party_cols
from .project import build_frame, project, raw_projection
from .seats import allocate

FRACS = [0.01, 0.02, 0.05, 0.10, 0.20, 0.40, 0.60, 0.80]
AGREEMENTS = {
    25: [("אמת", "מרצ"), ("ג", "שס"), ("מחל", "ט"), ("פה", "כן")],
    # 2026: five agreements filed by the 16.10.2026 deadline (Globes did=1001561042, Ynet hjextlj2gl, Kikar):
    # Likud-Religious Zionism, Shas-UTJ, Yashar-Democrats, Together(Bennett)-Yisrael Beiteinu, Ra'am-Joint List.
    # Letters per CEC list page https://www.gov.il/he/pages/candidates-lists-26. Not yet checked against CEC's own agreement notice.
    26: [("מחל", "ט"), ("שס", "ג"), ("דרך", "אמת"), ("רק", "ל"), ("עם", "ודם")],
}

def orders(frame, rng):
    n = len(frame)
    yield "random", rng.permutation(n)
    yield "small_first", np.argsort(frame.valid.values + rng.random(n))
    yield "large_first", np.argsort(-frame.valid.values - rng.random(n))
    yield "low_turnout_first", np.argsort(frame.x_turn.values + 1e-6 * rng.random(n))
    if "x_מחל" in frame:
        yield "low_likud_first", np.argsort(frame["x_מחל"].values + 1e-6 * rng.random(n))
        yield "high_likud_first", np.argsort(-frame["x_מחל"].values + 1e-6 * rng.random(n))

def seats_of(proj, ycols, agreements, threshold=0.0325):
    votes = {y[2:]: v for y, v in proj.items() if y != "y_other"}
    # "other" pools many tiny lists; none can pass the threshold individually
    return allocate(votes, agreements, threshold)

def run(T, frame, ycols, xcols, agreements, seeds=3, lam=5.0):
    vcols = ["v_" + y[2:] for y in ycols]
    truth_votes = dict(zip(ycols, frame[vcols].sum().values))
    tv = np.array(list(truth_votes.values())); tshare = tv / tv.sum()
    truth_seats = seats_of(truth_votes, ycols, agreements)
    rows = []
    for seed in range(seeds):
        rng = np.random.default_rng(seed)
        for oname, order in orders(frame, rng):
            if oname != "random" and seed > 0:
                continue
            for f in FRACS:
                n = int(round(f * len(frame)))
                mask = np.zeros(len(frame), bool); mask[order[:n]] = True
                for method, pr in (("ridge", project(frame, ycols, xcols, mask, lam)),
                                   ("raw_counted", raw_projection(frame, ycols, mask))):
                    pv = np.array(list(pr.values())); pshare = pv / pv.sum()
                    s = seats_of(pr, ycols, agreements)
                    keys = set(s) | set(truth_seats)
                    seat_err = sum(abs(s.get(k, 0) - truth_seats.get(k, 0)) for k in keys) / 2
                    rows.append(dict(T=T, order=oname, seed=seed, frac=f, method=method,
                                     share_mae_pp=100 * float(np.abs(pshare - tshare).mean()),
                                     share_max_pp=100 * float(np.abs(pshare - tshare).max()),
                                     seats_misallocated=seat_err))
    return pd.DataFrame(rows), truth_seats

def main():
    out = []
    for T in (26, 25, 24, 23, 22):
        cur = load_live(live_snapshots()[-1][1]) if T == 26 else load_history(T)
        prev = load_history(T - 1)
        frame, yc, xc = build_frame(cur, prev)
        ag = AGREEMENTS.get(T, [])
        df, ts = run(T, frame, yc, xc, ag)
        print(T, "stations", len(frame), "matched valid share %.3f" % (frame.valid[frame.matched].sum() / frame.valid.sum()))
        out.append(df)
    res = pd.concat(out)
    os.makedirs("results", exist_ok=True)
    res.to_csv("results/backtest.csv", index=False)
    print(res.groupby(["T", "method", "frac"])[["share_mae_pp", "seats_misallocated"]].mean().unstack([0]).round(2).to_string())

if __name__ == "__main__":
    main()
