"""Monte Carlo seat ranges from the latest live snapshot (or a backtest replay).

    python -m model.simulate            # live 2026 snapshot vs Knesset 25
    python -m model.simulate 25 0.05    # replay Knesset 25 with 5% of stations counted (random order)
"""
import sys, time, warnings
warnings.filterwarnings("ignore")
import numpy as np
from .load import load_history, load_live, live_snapshots
from .project import build_frame, project_draws
from .backtest import seats_of, AGREEMENTS

def simulate(frame, yc, xc, counted, ag, n_draws=200, seed=0):
    t0 = time.time()
    D = project_draws(frame, yc, xc, counted, n_draws, seed=seed)
    t1 = time.time()
    S = [seats_of(dict(zip(yc, d)), yc, ag) for d in D]
    t2 = time.time()
    lists = sorted({k for s in S for k in s})
    A = np.array([[s.get(k, 0) for k in lists] for s in S])
    out = {k: dict(median=float(np.median(A[:, i])), lo=float(np.quantile(A[:, i], .1)),
                   hi=float(np.quantile(A[:, i], .9)), p_in=float((A[:, i] > 0).mean()))
           for i, k in enumerate(lists)}
    return out, dict(draws_s=t1 - t0, seats_s=t2 - t1, n_draws=n_draws)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        T, f = int(sys.argv[1]), float(sys.argv[2])
        frame, yc, xc = build_frame(load_history(T), load_history(T - 1))
        rng = np.random.default_rng(0); m = np.zeros(len(frame), bool)
        m[rng.permutation(len(frame))[:int(f * len(frame))]] = True
    else:
        T = 26
        frame, yc, xc = build_frame(load_live(live_snapshots()[-1][1]), load_history(25))
        m = np.ones(len(frame), bool)  # all boxes in the file are counted; uncounted unknown (see README)
    out, tm = simulate(frame, yc, xc, m, AGREEMENTS.get(T, []))
    print("stations", len(frame), "counted", int(m.sum()), tm)
    for k, v in sorted(out.items(), key=lambda kv: -kv[1]["median"]):
        print(f"{k:6s} median {v['median']:5.1f}  80% [{v['lo']:.0f}, {v['hi']:.0f}]  P(in Knesset) {v['p_in']:.2f}")
