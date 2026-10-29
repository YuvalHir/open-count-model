"""swing-v1. See docs/prereg/swing_v1.md"""
import numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from .load import load_history, load_live, live_snapshots
from .project import build_frame, ridge_fit_predict
from .backtest import orders, seats_of, AGREEMENTS
def proj(frame, yc, xc, mask, mode, lam=5.0):
    c = frame[mask]; u = frame[~mask]; vc = ["v_" + y[2:] for y in yc]; cv = c[vc].sum().values
    ratio = c.valid.sum() / c.prev_valid.sum(); uv = u.prev_valid.values * ratio
    if mode == "base":
        P = ridge_fit_predict(c[xc].values, c[yc].values, np.sqrt(c.valid.values), u[xc].values, lam)
    else:
        w = c.valid.values; k = 1.0 if mode == "swing_full" else 0.5
        cur = np.clip(c[vc].values.sum(0) / w.sum(), 0.002, None)
        P = np.tile(cur, (len(u), 1))   # lists with no T-1 share (new lists): national current share, constant (implementation detail, same for all variants)
        for j, y in enumerate(yc):
            x = "x_" + y[2:]
            if x in frame:
                prev = max((c[x].values * w).sum() / w.sum(), 0.002)
                P[:, j] = u[x].values * np.exp(k * np.log(cur[j] / prev))
        P = P / np.clip(P.sum(1, keepdims=True), 1e-9, None)
    return dict(zip(yc, cv + (P * uv[:, None]).sum(0)))
def main():
    rows = []
    for T in (22, 23, 24, 25, 26):
        cur = load_live(live_snapshots()[-1][1]) if T == 26 else load_history(T)
        frame, yc, xc = build_frame(cur, load_history(T - 1)); ag = AGREEMENTS.get(T, [])
        missing = [y for y in yc if "x_" + y[2:] not in frame]
        if missing: print(T, "no x for", missing)
        vc = ["v_" + y[2:] for y in yc]; tv = frame[vc].sum().values; tsh = tv / tv.sum(); ts = seats_of(dict(zip(yc, tv)), yc, ag)
        for seed in range(3):
            rng = np.random.default_rng(seed)
            for on, order in orders(frame, rng):
                if on not in ("random", "low_likud_first", "small_first", "low_turnout_first") or (on != "random" and seed): continue
                for f in (0.01, 0.05, 0.20, 0.40):
                    mask = np.zeros(len(frame), bool); mask[order[:int(round(f * len(frame)))]] = True
                    for mode in ("base", "swing_full", "swing_half"):
                        pr = proj(frame, yc, xc, mask, mode); pv = np.array(list(pr.values())); psh = pv / pv.sum(); s = seats_of(pr, yc, ag)
                        se = sum(abs(s.get(k, 0) - ts.get(k, 0)) for k in set(s) | set(ts)) / 2
                        rows.append(dict(T=T, order=on, seed=seed, frac=f, mode=mode, share_mae_pp=100 * np.abs(psh - tsh).mean(), seats=se))
    d = pd.DataFrame(rows); d.to_csv("results/swing.csv", index=False)
    print(d.groupby(["order", "frac", "mode"])[["share_mae_pp", "seats"]].mean().round(3).unstack("mode").to_string())
    p = d.pivot_table(index=["T", "order", "seed", "frac"], columns="mode", values="share_mae_pp"); rng = np.random.default_rng(0)
    for m in ("swing_full", "swing_half"):
        diff = (p[m] - p["base"]).values; bs = [rng.choice(diff, len(diff)).mean() for _ in range(2000)]
        print(m, "paired diff pp %.4f CI [%.4f, %.4f]" % (diff.mean(), *np.percentile(bs, [2.5, 97.5])))
        print(" per T random:", (p[m] - p["base"]).xs("random", level="order").groupby("T").mean().round(3).to_dict())
if __name__ == "__main__": main()
