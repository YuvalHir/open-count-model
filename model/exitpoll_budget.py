"""Boxes vs interviews per box at fixed budgets, with design effect (pre-registered in docs/prereg/tv_miss_diagnosis.md, Q3).
Scenario: none (pure sampling error). Usage: OMP_NUM_THREADS=1 python3 -m model.exitpoll_budget T reps out.csv"""
import sys, numpy as np, pandas as pd
from .exitpoll import prepare, lie, pick, estimate
from .backtest import AGREEMENTS, seats_of
NN = [30, 60, 120, 240]; MM = [50, 100, 200, 400]
def run(T, reps=100, designs=("pps_ratio", "strat_prior")):
    D = prepare(T); letters = D["letters"]; ag = AGREEMENTS.get(T, []); yc = ["y_" + l for l in letters]
    shy = letters[int(np.argmax(D["truth"][:-1]))]; j = letters.index(shy); p = D["truth"][j]
    tseats = seats_of(dict(zip(yc, D["truth"] * 1e6)), yc, ag); Q = D["S"]; Qx = D["X"]; rows = []
    for design in designs:
        for n in NN:
            for m in MM:
                rng = np.random.default_rng([T, n, m, len(design)]); err = np.empty((reps, len(letters))); sm = np.empty(reps)
                for r in range(reps):
                    idx, wt = pick(D, design, n, rng); th = estimate(D, design, idx, wt, m, rng, Q, Qx)
                    err[r] = th - D["truth"]; s = seats_of(dict(zip(yc, th * 1e6)), yc, ag)
                    sm[r] = sum(abs(s.get(k, 0) - tseats.get(k, 0)) for k in set(s) | set(tseats)) / 2
                deff = err[:, j].var() / (p * (1 - p) / (n * m))
                rows.append(dict(T=T, design=design, n_places=n, m=m, budget=n * m, seats_out_of_place=sm.mean(), share_mae_pp=100 * np.abs(err).mean(), deff_top=deff))
    return pd.DataFrame(rows)
if __name__ == "__main__":
    T, reps, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]; run(T, reps).to_csv(out, index=False)
