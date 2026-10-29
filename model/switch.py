"""switch-v1: see docs/prereg/switch_v1.md"""
import sys, numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from .load import load_history
from .project import build_frame
from .backtest import orders, seats_of, AGREEMENTS
from . import round2
def one(T):
    cur = round2.cur_data(T); frame, yc, xc = build_frame(cur, load_history(T - 1)); ag = AGREEMENTS.get(T, [])
    vc = ["v_" + y[2:] for y in yc]; tv = frame[vc].sum().values; tsh = tv / tv.sum(); ts = seats_of(dict(zip(yc, tv)), yc, ag)
    xs = round2.shares_cols(xc); xl = [x[2:] for x in xs]; yl = [y[2:] for y in yc]; common = [l for l in xl if l in yl and l != "other"]
    Xs = frame[["x_" + l for l in common]].values; wp = frame.prev_valid.values.astype(float); tot = (Xs * wp[:, None]).sum(0) / wp.sum()
    G = lambda m: 100 * np.abs((Xs[m] * wp[m, None]).sum(0) / wp[m].sum() - tot).sum()
    nulls = {}; rows = []
    for seed in range(3):
        rng = np.random.default_rng(seed)
        for on, order in orders(frame, rng):
            if on not in ("random", "low_likud_first", "small_first", "low_turnout_first") or (on != "random" and seed): continue
            for f in (0.01, 0.05, 0.20, 0.40):
                n = int(round(f * len(frame))); mask = np.zeros(len(frame), bool); mask[order[:n]] = True
                if n not in nulls:
                    r2 = np.random.default_rng(12345); nulls[n] = np.percentile([G(np.isin(np.arange(len(frame)), r2.choice(len(frame), n, replace=False))) for _ in range(200)], 95)
                g = G(mask); sw = g > nulls[n]; res = {}
                for mode in ("base", "transfer_k002"):
                    pr = round2.proj(T, frame, yc, xc, mask, mode); pv = np.array(list(pr.values())); psh = pv / pv.sum(); s = seats_of(pr, yc, ag)
                    res[mode] = (100 * np.abs(psh - tsh).mean(), sum(abs(s.get(k, 0) - ts.get(k, 0)) for k in set(s) | set(ts)) / 2)
                for m, v in (("base", res["base"]), ("transfer", res["transfer_k002"]), ("switch", res["transfer_k002"] if sw else res["base"])):
                    rows.append(dict(T=T, order=on, seed=seed, frac=f, method=m, share_mae_pp=v[0], seats=v[1], g=g, thr=nulls[n], switched=int(sw)))
    return pd.DataFrame(rows)
if __name__ == "__main__":
    if sys.argv[1] == "merge":
        d = pd.concat([pd.read_csv(f"/tmp/switch_{T}.csv") for T in (20, 21, 23, 24, 25, 26)]); d.to_csv("results/switch.csv", index=False)
        d["set"] = np.where(d["T"] >= 23, "dev23-26", "holdout20-21")
        for k in ("share_mae_pp", "seats"): print(k); print(d.groupby(["set", "order", "frac", "method"])[k].mean().unstack("method").round(3).to_string())
        print("switch rate"); print(d[d.method == "switch"].groupby(["set", "order", "frac"]).switched.mean().unstack("frac").round(2).to_string())
    else: one(int(sys.argv[1])).to_csv(f"/tmp/switch_{sys.argv[1]}.csv", index=False)
