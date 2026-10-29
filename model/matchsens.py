"""matchsens-v1. See docs/prereg/matchsens_v1.md"""
import numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from .load import load_history, load_live, live_snapshots
from .project import build_frame, project
from .backtest import orders, seats_of, AGREEMENTS
def degrade(frame, xc, target, kind, rng):
    f = frame.copy(); m = f.matched.values.copy(); tot = f.valid.sum()
    idx = np.where(m)[0]
    order = rng.permutation(idx) if kind == "random" else idx[np.argsort(-f.valid.values[idx])]
    cur = f.valid.values[m].sum(); drop = []
    for i in order:
        if cur / tot <= target: break
        drop.append(i); cur -= f.valid.values[i]
    keep = m.copy(); keep[drop] = False
    cols = list(dict.fromkeys([c for c in xc if c not in ("x_turn", "x_logreg")] + ["x_turn", "x_logreg"]))
    w = np.where(keep, f.valid.values + 1e-9, 0.0); loc = f.loc_code.values
    wl = pd.Series(w).groupby(loc).transform("sum").values
    for c in cols + ["prev_valid"]:
        v = f[c].values.astype(float)
        if c == "prev_valid":
            num = pd.Series(np.where(keep, v, 0.0)).groupby(loc).transform("sum").values; den = pd.Series(keep.astype(float)).groupby(loc).transform("sum").values
        else:
            num = pd.Series(v * w).groupby(loc).transform("sum").values; den = wl
        nat = (v[keep] * (1 if c == "prev_valid" else w[keep])).sum() / (keep.sum() if c == "prev_valid" else w[keep].sum())
        mean = np.where(den > 0, num / np.where(den > 0, den, 1), nat)
        f[c] = np.where(keep, v, mean)
    return f, cur / tot
def main():
    rows = []
    for T in (22, 23, 24, 25, 26):
        cur = load_live(live_snapshots()[-1][1]) if T == 26 else load_history(T)
        frame, yc, xc = build_frame(cur, load_history(T - 1)); ag = AGREEMENTS.get(T, [])
        base = frame.valid[frame.matched].sum() / frame.valid.sum(); vc = ["v_" + y[2:] for y in yc]
        tv = frame[vc].sum().values; tsh = tv / tv.sum(); ts = seats_of(dict(zip(yc, tv)), yc, ag)
        for kind in ("random", "large_first"):
            for target in (None, 0.90, 0.85, 0.76, 0.65):
                if target is not None and target >= base: continue
                for seed in range(3):
                    rng = np.random.default_rng(100 + seed)
                    fr, got = (frame, base) if target is None else degrade(frame, xc, target, kind, rng)
                    if target is None and kind == "large_first": continue
                    for on, order in orders(fr, np.random.default_rng(seed)):
                        if on not in ("random", "low_likud_first") or (on != "random" and seed): continue
                        for f in (0.05, 0.20):
                            mask = np.zeros(len(fr), bool); mask[order[:int(round(f * len(fr)))]] = True
                            pr = project(fr, yc, xc, mask); pv = np.array(list(pr.values())); psh = pv / pv.sum(); s = seats_of(pr, yc, ag)
                            se = sum(abs(s.get(k, 0) - ts.get(k, 0)) for k in set(s) | set(ts)) / 2
                            rows.append(dict(T=T, kind=kind if target else "none", target=target or base, achieved=got, order=on, frac=f, share_mae_pp=100 * np.abs(psh - tsh).mean(), seats=se))
    d = pd.DataFrame(rows); d.to_csv("results/matchsens.csv", index=False)
    d["tgt"] = (d.target * 100).round(0)
    print(d[d.kind != "none"].groupby(["kind", "order", "frac", "tgt"])[["share_mae_pp", "seats"]].mean().round(3).unstack("tgt").to_string())
    print(d[d.kind == "none"].groupby(["T", "order", "frac"]).share_mae_pp.mean().round(3).unstack(["order", "frac"]).to_string())
if __name__ == "__main__": main()
