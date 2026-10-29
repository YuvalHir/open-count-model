"""Leave-one-election-out validation of the tuned choices (matching strategy, ridge lambda).

Development set = K22-K25 (the same data the choices were compared on, so those numbers are development numbers).
For each held-out election H: pick the (strategy, lambda) with the lowest mean share error on the other three
elections, then report the picked configuration on H next to the frozen default (tag matching-rules-v1) on H.
K26 is NOT a holdout: its observed count already guided design decisions, and its truth is not final.
Metric: mean absolute error of projected list shares (pp) at 5% and 20% counted, random order (3 seeds), plus
low-Likud-first at 20%; and seats misallocated at the same points. Orders are simulated.
"""
import itertools, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from .load import load_history
from .project import build_frame, project
from .backtest import seats_of, AGREEMENTS
STRATS = ["exact", "fill", "site", "site2"]; LAMS = [1.0, 5.0, 20.0]; DEFAULT = ("site", 5.0)

def score(T, st, lam):
    cur, prev = load_history(T), load_history(T - 1)
    fr, yc, xc = build_frame(cur, prev, st)
    vc = ["v_" + y[2:] for y in yc]; tv = fr[vc].sum().values; ts = seats_of(dict(zip(yc, tv)), yc, AGREEMENTS.get(T, []))
    out = {"share": [], "seats": []}
    for oname, seeds in (("random", range(3)), ("low", range(1))):
        for f in (0.05, 0.20):
            if oname == "low" and f == 0.05: continue
            for seed in seeds:
                rng = np.random.default_rng(seed)
                k = "x_מחל" if "x_מחל" in fr else "x_ג"
                order = rng.permutation(len(fr)) if oname == "random" else np.argsort(fr[k].values + 1e-6 * rng.random(len(fr)))
                m = np.zeros(len(fr), bool); m[order[:int(f * len(fr))]] = True
                pr = project(fr, yc, xc, m, lam); a = np.array(list(pr.values())); a /= a.sum()
                out["share"].append(100 * np.abs(a - tv / tv.sum()).mean())
                s = seats_of(pr, yc, AGREEMENTS.get(T, []))
                out["seats"].append(sum(abs(s.get(k2, 0) - ts.get(k2, 0)) for k2 in set(s) | set(ts)) / 2)
    return np.mean(out["share"]), np.mean(out["seats"])

def main():
    Ts = (22, 23, 24, 25)
    R = {(T, st, lam): score(T, st, lam) for T in Ts for st in STRATS for lam in LAMS}
    rows = []
    for H in Ts:
        others = [T for T in Ts if T != H]
        best = min(itertools.product(STRATS, LAMS), key=lambda c: np.mean([R[(T, *c)][0] for T in others]))
        dev = np.mean([R[(T, *best)][0] for T in others])
        rows.append(dict(held_out=H, picked=f"{best[0]}/lam={best[1]:g}", dev_share_mae=dev, held_share_mae=R[(H, *best)][0],
                         held_seats=R[(H, *best)][1], default_held_share_mae=R[(H, *DEFAULT)][0], default_held_seats=R[(H, *DEFAULT)][1],
                         exact_held_share_mae=R[(H, "exact", 5.0)][0], exact_held_seats=R[(H, "exact", 5.0)][1]))
    d = pd.DataFrame(rows); d.to_csv("results/loo.csv", index=False)
    pd.set_option("display.width", 220); print(d.round(3).to_string()); print(d.mean(numeric_only=True).round(3))
    pd.DataFrame([dict(T=T, strategy=s, lam=l, share_mae=v[0], seats=v[1]) for (T, s, l), v in R.items()]).to_csv("results/loo_grid.csv", index=False)

if __name__ == "__main__":
    main()
