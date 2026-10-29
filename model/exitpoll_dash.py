"""Grid for the interactive exit-poll dashboard (pre-registered: docs/prereg/dashboard_ideal_model.md).
Usage: OMP_NUM_THREADS=1 python3 -m model.exitpoll_dash T reps out.csv [design ...]"""
import sys, itertools, numpy as np, pandas as pd
from .exitpoll import prepare, pick, estimate, _refuse, HAREDI, ARAB
from .backtest import AGREEMENTS, seats_of
NN = [30, 60, 120, 240]; MM = [50, 100, 200, 400]
DES = ["pps_ratio", "strat_prior", "strat_prior_bk", "strat_prior_pastvote", "strat_greg_ps_bk", "strat_prior_tw"]
LIE = [("none", 0)] + [(p, l) for p in ("shy", "rand") for l in (5, 10, 20)]
NR = ["none", "nr", "nr_refuse"]
RIGHT = {22: {"מחל", "שס", "ג", "טב"}, 23: {"מחל", "שס", "ג", "טב"}, 24: {"מחל", "שס", "ג", "ט", "ב"}, 25: {"מחל", "שס", "ג", "ט"}, 26: {"מחל", "שס", "ג", "ט", "ב"}}

def answers(P, letters, shy, pat, lv, nr):
    P = P.copy(); K = P.shape[1]; j = letters.index(shy)
    if pat == "rand":
        u = np.ones(K); u[-1] = 0; u /= u.sum(); f = lv / 100; P = (1 - f) * P + f * u
    if pat == "shy":
        moved = lv / 100 * P[:, j]; rest = P.copy(); rest[:, j] = 0
        rest = rest / np.clip(rest.sum(1, keepdims=True), 1e-12, None); P[:, j] -= moved; P += moved[:, None] * rest
    if nr != "none":
        for k, l in enumerate(letters):
            if l in HAREDI: P[:, k] *= 0.5
            elif l in ARAB: P[:, k] *= 0.6
    return P / P.sum(1, keepdims=True)

def run(T, reps=60, designs=DES):
    D = prepare(T); D0 = D; letters = D["letters"]; ag = AGREEMENTS.get(T, []); yc = ["y_" + l for l in letters]
    shy = letters[int(np.argmax(D["truth"][:-1]))]
    tseats = seats_of(dict(zip(yc, D["truth"] * 1e6)), yc, ag)
    def blocs(s):
        f = lambda k: k[2:] if k.startswith("y_") else k
        return (sum(v for k, v in s.items() if f(k) in RIGHT[T]), sum(v for k, v in s.items() if f(k) in ARAB))
    tr, ta = blocs(tseats); rows = []
    for (pat, lv), nr in itertools.product(LIE, NR):
        Q = answers(D["S"], letters, shy, pat, lv, nr); Qx = answers(D["X"], letters, shy, pat, lv, nr)
        for di, design in enumerate(designs):
            base = "strat_prior" if design == "strat_prior_tw" else design
            if design == "strat_prior_tw":   # turnout-weighted: box sizes from (noisy, 3%) turnout known on the day, instead of last election's turnout
                D = dict(D0); D["sz"] = D0["w"] * np.exp(0.03 * np.random.default_rng(5).standard_normal(len(D0["w"])))
            else: D = D0
            for n, m in itertools.product(NN, MM):
                rng = np.random.default_rng([T, di, n, m, lv, len(pat), len(nr)]); mae = np.empty(reps); sm = np.empty(reps); br = np.empty(reps); ba = np.empty(reps)
                for r in range(reps):
                    idx, wt = pick(D, base, n, rng)
                    if nr == "nr_refuse": idx, wt = _refuse(D, idx, wt, base, "hard_both", rng)
                    th = (D["X"] * D["sz"][:, None]).sum(0) / D["sz"].sum() if (idx is None or len(idx) == 0) else estimate(D, base, idx, wt, m, rng, Q, Qx)
                    mae[r] = 100 * np.abs(th - D["truth"]).mean(); s = seats_of(dict(zip(yc, th * 1e6)), yc, ag)
                    sm[r] = sum(abs(s.get(k, 0) - tseats.get(k, 0)) for k in set(s) | set(tseats)) / 2
                    a, b = blocs(s); br[r] = abs(a - tr); ba[r] = abs(b - ta)
                rows.append(dict(T=T, design=design, n=n, m=m, pat=pat, lv=lv, nr=nr, mae_pp=mae.mean(), seats_oop=sm.mean(), right_err=br.mean(), arab_err=ba.mean()))
    return pd.DataFrame(rows)
if __name__ == "__main__":
    T, reps, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]; ds = sys.argv[4:] or DES
    run(T, reps, ds).to_csv(out, index=False)
