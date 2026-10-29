"""sizemodel-v1. See docs/prereg/sizemodel_v1.md"""
import numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from .load import load_history, load_live, live_snapshots
from .project import build_frame, ridge_fit_predict
from .backtest import orders, seats_of, AGREEMENTS
def proj(frame, yc, xc, mask, mode, lam=5.0):
    c = frame[mask]; u = frame[~mask]; vc = ["v_" + y[2:] for y in yc]; cv = c[vc].sum().values
    ratio = c.valid.sum() / c.prev_valid.sum(); uv = u.prev_valid.values * ratio
    if mode == "size_ridge":
        ok = c.prev_valid.values > 0
        t = np.log((c.valid.values + 1) / (c.prev_valid.values + 1))[ok][:, None]
        g = ridge_fit_predict(c[xc].values[ok], np.hstack([t, t]), np.sqrt(c.valid.values[ok]) + 0, u[xc].values, lam)  # shares-normalised: use raw fit below
        mu, sd = c[xc].values[ok].mean(0), c[xc].values[ok].std(0) + 1e-9
        A = np.hstack([np.ones((ok.sum(), 1)), (c[xc].values[ok] - mu) / sd]); B = np.hstack([np.ones((len(u), 1)), (u[xc].values - mu) / sd])
        w = np.sqrt(c.valid.values[ok]); R = lam * np.eye(A.shape[1]); R[0, 0] = 0
        beta = np.linalg.solve(A.T @ (A * w[:, None]) + R, A.T @ (t[:, 0] * w))
        lr = np.clip(B @ beta, -0.7, 0.7)
        uv = np.where(u.prev_valid.values > 0, (u.prev_valid.values + 1) * np.exp(lr) - 1, np.median(c.valid.values))
        uv = np.clip(uv, 0, None)
    elif mode == "size_reg":
        r2 = c.valid.sum() / max(c.registered.sum(), 1)   # not used in production; placeholder replaced below
        prev_reg = np.exp(frame.x_logreg.values)          # T-1 registered
        r = c.valid.sum() / np.exp(c.x_logreg.values).sum(); uv = np.exp(u.x_logreg.values) * r
    P = ridge_fit_predict(c[xc].values, c[yc].values, np.sqrt(c.valid.values), u[xc].values, lam)
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
                    for mode in ("base", "size_ridge", "size_reg"):
                        pr = proj(frame, yc, xc, mask, mode); pv = np.array(list(pr.values())); psh = pv / pv.sum(); s = seats_of(pr, yc, ag)
                        se = sum(abs(s.get(k, 0) - ts.get(k, 0)) for k in set(s) | set(ts)) / 2
                        rows.append(dict(T=T, order=on, seed=seed, frac=f, mode=mode, share_mae_pp=100 * np.abs(psh - tsh).mean(), seats=se))
    d = pd.DataFrame(rows); d.to_csv("results/sizemodel.csv", index=False)
    print(d.groupby(["order", "frac", "mode"])[["share_mae_pp", "seats"]].mean().round(3).unstack("mode").to_string())
    p = d.pivot_table(index=["T", "order", "seed", "frac"], columns="mode", values="share_mae_pp")
    rng = np.random.default_rng(0)
    for m in ("size_ridge", "size_reg"):
        diff = (p[m] - p["base"]).values; bs = [rng.choice(diff, len(diff)).mean() for _ in range(2000)]
        print(m, "mean paired diff pp %.4f CI [%.4f, %.4f]" % (diff.mean(), *np.percentile(bs, [2.5, 97.5])))
        print(" per T (random order):", (p[m] - p["base"]).xs("random", level="order").groupby("T").mean().round(3).to_dict())
        print(" per T (all biased):", (p[m] - p["base"]).drop("random", level="order").groupby("T").mean().round(3).to_dict())
if __name__ == "__main__": main()
