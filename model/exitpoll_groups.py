"""Signed group-level seat error in the exit-poll simulation (pre-registered: docs/prereg/tv_miss_diagnosis.md).
Usage: OMP_NUM_THREADS=1 python3 -m model.exitpoll_groups T reps out.csv"""
import sys, numpy as np, pandas as pd
from .exitpoll import prepare, lie, pick, estimate, _refuse, HAREDI, ARAB, DESIGNS
from .backtest import AGREEMENTS, seats_of
SC = ["none", "noise10", "shy15", "refuse20", "hard_nr", "place_refuse", "hard_both"]
def run(T, reps=100, n=60, m=100, designs=("pps_ratio", "strat_prior")):
    D = prepare(T); letters = D["letters"]; ag = AGREEMENTS.get(T, []); yc = ["y_" + l for l in letters]
    shy = letters[int(np.argmax(D["truth"][:-1]))]
    tseats = seats_of(dict(zip(yc, D["truth"] * 1e6)), yc, ag)
    def gs(s):
        g = dict(Likud=0, Haredi=0, Arab=0, Rest=0)
        for k, v in s.items():
            l = k[2:] if k.startswith("y_") else k
            if l == shy: g["Likud"] += v      # largest list; Likud in K22-25 except K22/K23 where it is Blue & White/Likud, see top_list column
            elif l in HAREDI: g["Haredi"] += v
            elif l in ARAB: g["Arab"] += v
            else: g["Rest"] += v
        return g
    tg = gs(tseats); rows = []
    for sc in SC:
        Q = lie(D["S"], letters, sc, shy); Qx = lie(D["X"], letters, sc, shy)
        for di, design in enumerate(designs):
            rng = np.random.default_rng([T, SC.index(sc), di, 777]); acc = np.zeros((reps, 4)); keys = ["Likud", "Haredi", "Arab", "Rest"]
            for r in range(reps):
                idx, wt = pick(D, design, n, rng)
                if sc in ("place_refuse", "hard_both"): idx, wt = _refuse(D, idx, wt, design, sc, rng)
                th = (D["X"] * D["sz"][:, None]).sum(0) / D["sz"].sum() if (idx is None or len(idx) == 0) else estimate(D, design, idx, wt, m, rng, Q, Qx)
                g = gs(seats_of(dict(zip(yc, th * 1e6)), yc, ag)); acc[r] = [g[k] - tg[k] for k in keys]
            for j, k in enumerate(keys):
                rows.append(dict(T=T, scenario=sc, design=design, group=k, top_list=shy, signed_seats=acc[:, j].mean(), sd=acc[:, j].std(), final_seats=tg[k]))
    return pd.DataFrame(rows)
if __name__ == "__main__":
    T, reps, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    df = run(T, reps); df.to_csv(out, index=False); print(df.groupby(["scenario", "design", "group"]).signed_seats.mean().round(2).unstack("group").to_string())
