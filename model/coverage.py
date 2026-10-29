"""Check that seat/bloc intervals from project_draws contain the truth about as often as claimed."""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from .load import load_history, load_live, live_snapshots
from .project import build_frame, project_draws
from .backtest import orders, seats_of, AGREEMENTS, FRACS

def run(T, n_draws=150, fracs=(0.02, 0.05, 0.20, 0.40), seeds=2, q=(0.1, 0.9)):
    cur = load_live(live_snapshots()[-1][1]) if T == 26 else load_history(T)
    frame, yc, xc = build_frame(cur, load_history(T - 1))
    ag = AGREEMENTS.get(T, [])
    vcols = ["v_" + y[2:] for y in yc]
    truth = seats_of(dict(zip(yc, frame[vcols].sum().values)), yc, ag)
    rows = []
    for seed in range(seeds):
        rng = np.random.default_rng(100 + seed)
        order = dict(orders(frame, rng))["random"]
        for f in fracs:
            n = int(round(f * len(frame))); m = np.zeros(len(frame), bool); m[order[:n]] = True
            D = project_draws(frame, yc, xc, m, n_draws, seed=seed)
            S = [seats_of(dict(zip(yc, d)), yc, ag) for d in D]
            for k in sorted(set(truth) | {x for s in S for x in s}):
                arr = np.array([s.get(k, 0) for s in S])
                lo, hi = np.quantile(arr, q)
                rows.append(dict(T=T, seed=seed, frac=f, list=k, truth=truth.get(k, 0), lo=lo, hi=hi,
                                 hit=bool(lo <= truth.get(k, 0) <= hi), width=hi - lo))
    return pd.DataFrame(rows)

if __name__ == "__main__":
    r = pd.concat([run(T) for T in (25, 23, 22)])
    r.to_csv("out/coverage.csv", index=False)
    print(r.groupby("frac")[["hit", "width"]].mean().round(2))
    print(r.groupby(["T", "frac"]).hit.mean().unstack().round(2))
