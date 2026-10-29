"""Monte Carlo of respondent lying (pre-registered: docs/prereg/lies_montecarlo.md, tag lies-mc-v1).
Usage: OMP_NUM_THREADS=1 python3 -m model.lies_mc T draws out.csv"""
import sys, numpy as np, pandas as pd
from .exitpoll import prepare, pick, estimate
from .backtest import AGREEMENTS, seats_of
DES = ["pps_ratio", "strat_prior", "strat_greg_ps_bk", "strat_prior_pastvote"]
P_LIE, H_MAX = 0.35, 0.25   # pre-registered prior; the mild post-hoc sensitivity run sets 0.15, 0.10 via argv
SIZES = [(60, 100), (120, 200)]; REG = ["R1", "R2", "R3"]

def draw_pattern(truth, K, rng, regime):
    big = [j for j in range(K - 1) if truth[j] >= 0.03]
    hide = {}; dirs = {}
    for j in big:
        if rng.random() < P_LIE:
            hide[j] = rng.uniform(0, H_MAX); others = [k for k in big if k != j]
            if not others: continue
            if regime == "R1":
                d = np.zeros(K); d[rng.choice(others)] = 1
            else:
                d = np.zeros(K); d[others] = rng.dirichlet(np.ones(len(others)))
            dirs[j] = d
    return hide, dirs

def apply(P, hide, dirs):
    P = P.copy()
    for j, h in hide.items():
        if j not in dirs: continue
        moved = h * P[:, j]; P[:, j] -= moved; P += moved[:, None] * dirs[j][None, :]
    return P / P.sum(1, keepdims=True)

def run(T, draws):
    D = prepare(T); letters = D["letters"]; K = len(letters); ag = AGREEMENTS.get(T, []); yc = ["y_" + l for l in letters]
    tseats = seats_of(dict(zip(yc, D["truth"] * 1e6)), yc, ag); rows = []
    for ri, reg in enumerate(REG):
        for di, design in enumerate(DES):
            for (n, m) in SIZES:
                rng = np.random.default_rng([T, ri, di, n]); prng = np.random.default_rng([T, ri, 99, n])
                for r in range(draws):
                    hide, dirs = draw_pattern(D["truth"], K, prng, reg)
                    Q = apply(D["S"], hide, dirs); Qx = apply(D["X"], hide, dirs) if reg != "R3" else D["X"]
                    idx, wt = pick(D, design, n, rng)
                    th = estimate(D, design, idx, wt, m, rng, Q, Qx)
                    s = seats_of(dict(zip(yc, th * 1e6)), yc, ag)
                    oop = sum(abs(s.get(k, 0) - tseats.get(k, 0)) for k in set(s) | set(tseats)) / 2
                    rows.append(dict(T=T, regime=reg, design=design, n=n, m=m, draw=r, seats_oop=oop, mae_pp=100 * np.abs(th - D["truth"]).mean(), n_lying=len(dirs), mean_hide=float(np.mean([hide[j] for j in dirs])) if dirs else 0.0))
    return pd.DataFrame(rows)
if __name__ == "__main__":
    if len(sys.argv) > 5: P_LIE, H_MAX = float(sys.argv[4]), float(sys.argv[5])
    run(int(sys.argv[1]), int(sys.argv[2])).to_csv(sys.argv[3], index=False)
