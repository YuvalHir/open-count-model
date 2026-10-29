"""round2-v1: selection diagnostic (idea 1), importance weights (idea 2), prior-centred transfer model (idea 3). See docs/prereg/round2_v1.md"""
import sys, numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from .load import load_history, load_live, live_snapshots
from .project import build_frame, ridge_fit_predict
from .backtest import orders, seats_of, AGREEMENTS
def cur_data(T): return load_live(live_snapshots()[-1][1]) if T == 26 else load_history(T)
def shares_cols(xc): return [c for c in xc if c.startswith("x_") and c not in ("x_turn", "x_logreg")]
def logistic_w(X, lab, l2=1.0, it=25):
    mu, sd = X.mean(0), X.std(0) + 1e-9; A = np.hstack([np.ones((len(X), 1)), (X - mu) / sd]); b = np.zeros(A.shape[1]); R = l2 * np.eye(A.shape[1]); R[0, 0] = 0
    for _ in range(it):
        p = 1 / (1 + np.exp(-np.clip(A @ b, -30, 30))); W = p * (1 - p) + 1e-6
        b = b + np.linalg.solve(A.T @ (A * W[:, None]) + R, A.T @ (lab - p) - R @ b)
    return 1 / (1 + np.exp(-np.clip(A @ b, -30, 30)))
def proj_simplex(M):
    U = -np.sort(-M, axis=1); css = np.cumsum(U, 1) - 1; k = np.arange(1, M.shape[1] + 1); cond = U - css / k > 0
    rho = cond.sum(1); th = css[np.arange(len(M)), rho - 1] / rho; return np.clip(M - th[:, None], 0, None)
def fit_P(X, Y, w, P0, kappa, iters=300):
    W = w.sum(); G = X.T @ (X * w[:, None]); L = np.linalg.eigvalsh(G).max() + kappa * W
    XtY = X.T @ (Y * w[:, None]); P = P0.copy()
    for _ in range(iters):
        grad = G @ P - XtY + kappa * W * (P - P0); P = proj_simplex(P - grad / L)
    return P
def letters_of(frame, yc):
    xs = shares_cols(list(frame.columns)); return [c[2:] for c in xs], [y[2:] for y in yc]
_P0 = {}
def prior(T, xl, yl):
    """P0 from previous pair (T-2 -> T-1, all places, past data only), mapped by letter to T-1 lists -> T lists. Missing rows: identity if the list exists in T, else national mix."""
    if T not in _P0:
        fr, yc2, xc2 = build_frame(load_history(T - 1), load_history(T - 2)); xs2 = shares_cols(xc2); xl2 = [c[2:] for c in xs2]; yl2 = [y[2:] for y in yc2]
        w = fr.valid.values.astype(float); Y = fr[yc2].values; X = fr[xs2].values
        P = fit_P(X, Y, w, np.tile(Y.T @ w / w.sum(), (len(xl2), 1)), 0.0); _P0[T] = (xl2, yl2, P, Y.T @ w / w.sum())
    xl2, yl2, P2, nat = _P0[T]; P0 = np.zeros((len(xl), len(yl)))
    for a, la in enumerate(xl):
        if la in xl2 and la != "other":
            row = P2[xl2.index(la)]
            for b, lb in enumerate(yl):
                if lb in yl2: P0[a, b] = row[yl2.index(lb)]
        elif la in yl: P0[a, yl.index(la)] = 1.0
        else:
            for b, lb in enumerate(yl):
                if lb in yl2: P0[a, b] = nat[yl2.index(lb)]
    s = P0.sum(1, keepdims=True); P0 = np.where(s > 0, P0 / np.clip(s, 1e-9, None), 1.0 / P0.shape[1]); return P0
def proj(T, frame, yc, xc, mask, mode, lam=5.0):
    c = frame[mask]; u = frame[~mask]; vc = ["v_" + y[2:] for y in yc]; cv = c[vc].sum().values
    uv = u.prev_valid.values * (c.valid.sum() / c.prev_valid.sum()); wt = np.sqrt(c.valid.values)
    if mode == "iw":
        lab = np.r_[np.zeros(len(c)), np.ones(len(u))]; X = np.vstack([c[xc].values, u[xc].values]); q = np.clip(logistic_w(X, lab), 1e-4, 1 - 1e-4)[:len(c)]
        r = q / (1 - q) * (len(c) / len(u)); w = np.clip(r / (0.5 * r + 0.5), 0.1, 10); w = w / w.mean(); wt = wt * w
    if mode.startswith("transfer"):
        kappa = {"transfer_k002": 0.02, "transfer_k02": 0.2}[mode]
        xs = shares_cols(xc); xl, yl = [x[2:] for x in xs], [y[2:] for y in yc]
        P = fit_P(c[xs].values, c[yc].values, c.valid.values.astype(float), prior(T, xl, yl), kappa)
        S = u[xs].values @ P; S = S / np.clip(S.sum(1, keepdims=True), 1e-9, None)
    else:
        S = ridge_fit_predict(c[xc].values, c[yc].values, wt, u[xc].values, lam)
    return dict(zip(yc, cv + (S * uv[:, None]).sum(0)))
MODES = ("base", "iw", "transfer_k002", "transfer_k02")
def one(T):
    cur = cur_data(T); frame, yc, xc = build_frame(cur, load_history(T - 1)); ag = AGREEMENTS.get(T, [])
    vc = ["v_" + y[2:] for y in yc]; tv = frame[vc].sum().values; tsh = tv / tv.sum(); ts = seats_of(dict(zip(yc, tv)), yc, ag)
    xs = shares_cols(xc); xl = [x[2:] for x in xs]; yl = [y[2:] for y in yc]; common = [l for l in xl if l in yl and l != "other"]
    Xs = frame[["x_" + l for l in common]].values; Ys = frame[["y_" + l for l in common]].values; wv = frame.valid.values.astype(float); wp = frame.prev_valid.values.astype(float)
    rows = []
    for seed in range(3):
        rng = np.random.default_rng(seed)
        for on, order in orders(frame, rng):
            if on not in ("random", "low_likud_first", "small_first", "low_turnout_first") or (on != "random" and seed): continue
            for f in (0.01, 0.05, 0.20, 0.40):
                mask = np.zeros(len(frame), bool); mask[order[:int(round(f * len(frame)))]] = True; un = ~mask
                g = 100 * np.abs((Xs[mask] * wp[mask, None]).sum(0) / wp[mask].sum() - (Xs * wp[:, None]).sum(0) / wp.sum()).sum()
                sw = lambda m: (Ys[m] * wv[m, None]).sum(0) / wv[m].sum() - (Xs[m] * wp[m, None]).sum(0) / wp[m].sum()
                h = 100 * np.abs(sw(mask) - sw(un)).sum()
                for mode in MODES:
                    if mode.startswith("transfer") and T < 23: continue
                    pr = proj(T, frame, yc, xc, mask, mode); pv = np.array(list(pr.values())); psh = pv / pv.sum(); s = seats_of(pr, yc, ag)
                    se = sum(abs(s.get(k, 0) - ts.get(k, 0)) for k in set(s) | set(ts)) / 2
                    rows.append(dict(T=T, order=on, seed=seed, frac=f, mode=mode, share_mae_pp=100 * np.abs(psh - tsh).mean(), seats=se, g=g, h=h))
    return pd.DataFrame(rows)
def merge():
    d = pd.concat([pd.read_csv(f"/tmp/round2_{T}.csv") for T in range(22, 27)]); d.to_csv("results/round2.csv", index=False)
    print(d.groupby(["order", "frac", "mode"]).share_mae_pp.mean().round(3).unstack("mode").to_string())
    b = d[d["mode"] == "base"]; from math import isnan
    for k in ("g", "h"): print("spearman MAE vs", k, round(b[["share_mae_pp", k]].corr(method="spearman").iloc[0, 1], 3))
    print(b.groupby(["order", "frac"])[["g", "h", "share_mae_pp"]].mean().round(2).to_string())
if __name__ == "__main__":
    merge() if sys.argv[1] == "merge" else one(int(sys.argv[1])).to_csv(f"/tmp/round2_{sys.argv[1]}.csv", index=False)
