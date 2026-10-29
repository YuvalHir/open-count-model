"""holdout-v1: frozen method on K19-21 (never scored before). See docs/prereg/holdout_v1.md"""
import sys, numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from .load import load_history
from .project import build_frame, project, raw_projection
from .backtest import orders, seats_of, FRACS
from . import round2
def one(T):
    cur, prev = load_history(T), load_history(T - 1); frame, yc, xc = build_frame(cur, prev)
    vc = ["v_" + y[2:] for y in yc]; tv = frame[vc].sum().values; tsh = tv / tv.sum(); ts = seats_of(dict(zip(yc, tv)), yc, [])
    matched = frame.valid[frame.matched].sum() / frame.valid.sum(); rows = []
    for seed in range(3):
        rng = np.random.default_rng(seed)
        for on, order in orders(frame, rng):
            if on != "random" and seed: continue
            for f in FRACS:
                mask = np.zeros(len(frame), bool); mask[order[:int(round(f * len(frame)))]] = True
                meths = [("ridge", lambda: project(frame, yc, xc, mask)), ("raw_counted", lambda: raw_projection(frame, yc, mask))]
                if T >= 20 and on in ("random", "low_likud_first", "small_first", "low_turnout_first") and f in (0.01, 0.05, 0.2, 0.4):
                    meths.append(("transfer_k002", lambda: round2.proj(T, frame, yc, xc, mask, "transfer_k002")))
                for m, fn in meths:
                    pr = fn(); pv = np.array(list(pr.values())); psh = pv / pv.sum(); s = seats_of(pr, yc, [])
                    se = sum(abs(s.get(k, 0) - ts.get(k, 0)) for k in set(s) | set(ts)) / 2
                    rows.append(dict(T=T, order=on, seed=seed, frac=f, method=m, share_mae_pp=100 * np.abs(psh - tsh).mean(), seats=se, matched_votes_pct=100 * matched, boxes=len(frame)))
    return pd.DataFrame(rows)
if __name__ == "__main__":
    if sys.argv[1] == "merge":
        d = pd.concat([pd.read_csv(f"/tmp/holdout_{T}.csv") for T in (19, 20, 21)]); d.to_csv("results/holdout.csv", index=False)
        print(d.groupby("T")[["matched_votes_pct", "boxes"]].first().round(1))
        print(d[(d.order == "random") & d.frac.isin([0.05, 0.2])].groupby(["T", "frac", "method"])[["share_mae_pp", "seats"]].mean().round(2).unstack("method").to_string())
        print(d[(d.order == "low_likud_first") & d.frac.isin([0.01, 0.05, 0.2])].groupby(["T", "frac", "method"])[["share_mae_pp", "seats"]].mean().round(2).unstack("method").to_string())
        print(d[(d.order == "low_turnout_first") & (d.frac == 0.2)].groupby(["T", "method"]).share_mae_pp.mean().round(2).unstack())
    else: one(int(sys.argv[1])).to_csv(f"/tmp/holdout_{sys.argv[1]}.csv", index=False)
