"""Compare place-matching strategies: share of votes matched, quality of the matched profile,
and the effect on projection error (ridge, 10% and 20% counted) in a random and a biased order."""
import sys, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from .load import load_history, load_live, live_snapshots
from .project import build_frame, project
from .backtest import seats_of, AGREEMENTS

STRATS = sys.argv[1].split(",") if len(sys.argv) > 1 else ["exact", "fill", "site", "site2"]
OUT = sys.argv[2] if len(sys.argv) > 2 else "results/matching.csv"

def share_err(pr, truth):
    a = np.array(list(pr.values())); a /= a.sum(); b = truth / truth.sum()
    return 100 * np.abs(a - b).mean()

def main():
    rows = []
    for T in (22, 23, 24, 25, 26):
        cur = load_live(live_snapshots()[-1][1]) if T == 26 else load_history(T)
        prev = load_history(T - 1)
        for st in STRATS:
            fr, yc, xc = build_frame(cur, prev, st)
            vc = ["v_" + y[2:] for y in yc]; tv = fr[vc].sum().values
            ts = seats_of(dict(zip(yc, tv)), yc, AGREEMENTS.get(T, []))
            mv = fr.valid[fr.matched].sum() / fr.valid.sum()
            # profile quality: matched stations only, distance between this share vector and the matched previous profile
            # (lists differ across elections, so use only the same-letter lists present in both)
            r = dict(T=T, strategy=st, matched_votes_pct=100 * mv)
            for k in ("מחל", "ג", "שס"):
                if "y_" + k in fr:   # error of the matched previous-election profile for this list, all places, vote-weighted, percentage points
                    r["profile_MAE_" + k] = 100 * float(np.average(np.abs(fr["y_" + k] - fr["x_" + k]), weights=fr.valid))
            for oname in ("random", "low_likud_first"):
                for f in (0.05, 0.20):
                    errs, serr = [], []
                    for seed in range(4 if oname == "random" else 1):
                        rng = np.random.default_rng(seed)
                        if oname == "random":
                            order = rng.permutation(len(fr))
                        else:
                            k = "x_מחל" if "x_מחל" in fr else "x_ג"
                            order = np.argsort(fr[k].values + 1e-6 * rng.random(len(fr)))
                        m = np.zeros(len(fr), bool); m[order[:int(f * len(fr))]] = True
                        pr = project(fr, yc, xc, m)
                        errs.append(share_err(pr, tv))
                        s = seats_of(pr, yc, AGREEMENTS.get(T, []))
                        serr.append(sum(abs(s.get(k, 0) - ts.get(k, 0)) for k in set(s) | set(ts)) / 2)
                    r[f"{oname}_{int(f*100)}_shareMAE"] = np.mean(errs)
                    r[f"{oname}_{int(f*100)}_seats"] = np.mean(serr)
            rows.append(r)
    d = pd.DataFrame(rows)
    d.to_csv(OUT, index=False)
    pd.set_option("display.width", 250)
    print(d.round(2).to_string())
    print(d.groupby("strategy").mean(numeric_only=True).drop(columns="T").round(2).to_string())

if __name__ == "__main__":
    main()
