"""decomp-v1: oracle decomposition of projection error (size vs share). See docs/prereg/decomp_v1.md"""
import numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from .load import load_history, load_live, live_snapshots
from .project import build_frame, ridge_fit_predict
from .backtest import orders, seats_of, AGREEMENTS
def proj(frame, yc, xc, mask, mode, lam=5.0):
    c = frame[mask]; u = frame[~mask]; vc = ["v_" + y[2:] for y in yc]
    cv = c[vc].sum().values
    ratio = c.valid.sum() / c.prev_valid.sum()
    uv = u.prev_valid.values * ratio
    P = ridge_fit_predict(c[xc].values, c[yc].values, np.sqrt(c.valid.values), u[xc].values, lam)
    if mode in ("oracle_size", "oracle_both"): uv = u.valid.values.astype(float)
    if mode in ("oracle_share", "oracle_both"): P = u[vc].values / np.clip(u.valid.values[:, None], 1, None)
    return dict(zip(yc, cv + (P * uv[:, None]).sum(0)))
def main():
    rows = []
    for T in (22, 23, 24, 25, 26):
        cur = load_live(live_snapshots()[-1][1]) if T == 26 else load_history(T)
        frame, yc, xc = build_frame(cur, load_history(T - 1)); ag = AGREEMENTS.get(T, [])
        vc = ["v_" + y[2:] for y in yc]; tv = frame[vc].sum().values; tsh = tv / tv.sum(); ts = seats_of(dict(zip(yc, tv)), yc, ag)
        for seed in range(3):
            rng = np.random.default_rng(seed)
            for on, order in orders(frame, rng):
                if on not in ("random", "low_likud_first", "small_first", "low_turnout_first") or (on != "random" and seed): continue
                for f in (0.05, 0.20):
                    mask = np.zeros(len(frame), bool); mask[order[:int(round(f * len(frame)))]] = True
                    for mode in ("base", "oracle_size", "oracle_share", "oracle_both"):
                        pr = proj(frame, yc, xc, mask, mode); pv = np.array(list(pr.values())); psh = pv / pv.sum(); s = seats_of(pr, yc, ag)
                        se = sum(abs(s.get(k, 0) - ts.get(k, 0)) for k in set(s) | set(ts)) / 2
                        rows.append(dict(T=T, order=on, seed=seed, frac=f, mode=mode, share_mae_pp=100 * np.abs(psh - tsh).mean(), seats=se))
    d = pd.DataFrame(rows); d.to_csv("results/decomp.csv", index=False)
    g = d.groupby(["order", "frac", "mode"])[["share_mae_pp", "seats"]].mean().round(3).unstack("mode"); print(g.to_string())
    print(d.groupby(["T", "mode"]).share_mae_pp.mean().unstack().round(3).to_string())
if __name__ == "__main__": main()
