"""round3-v1: transfer diagnostics, severity-graded orders, offset ridge, prequential stacking. See docs/prereg/round3_v1.md"""
import sys, numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from .load import load_history
from .project import build_frame, ridge_fit_predict
from .backtest import seats_of, AGREEMENTS
from . import round2
from .round2 import shares_cols, fit_P, prior, cur_data
BETAS = (0, 0.5, 1, 2, 4, 8); FR = (0.01, 0.05, 0.20, 0.40); LAMS = (1e2, 1e3, 1e4, 1e5, 1e6, 1e7)
def offset_S(Xc, Xsc, Yc, wc, P0, Xu, Xsu, lam):
    mu, sd = Xc.mean(0), Xc.std(0) + 1e-9; A = np.hstack([np.ones((len(Xc), 1)), (Xc - mu) / sd]); B = np.hstack([np.ones((len(Xu), 1)), (Xu - mu) / sd])
    R = lam * np.eye(A.shape[1]); R[0, 0] = 0; res = Yc - Xsc @ P0
    beta = np.linalg.solve(A.T @ (A * wc[:, None]) + R, A.T @ (res * wc[:, None])); S = np.clip(Xsu @ P0 + B @ beta, 0, None)
    return S / np.clip(S.sum(1, keepdims=True), 1e-9, None)
def eb_lambda(T):
    cur, prev = load_history(T - 1), load_history(T - 2); fr, yc2, xc2 = build_frame(cur, prev); xs2 = shares_cols(xc2)
    P0 = prior(T - 1, [c[2:] for c in xs2], [y[2:] for y in yc2]); rng = np.random.default_rng(0); half = rng.random(len(fr)) < 0.5; w = fr.valid.values.astype(float)
    X, Xs, Y = fr[xc2].values, fr[xs2].values, fr[yc2].values; best = None
    for lam in LAMS:
        e = 0
        for a, b in ((half, ~half), (~half, half)):
            S = offset_S(X[a], Xs[a], Y[a], w[a], P0, X[b], Xs[b], lam); e += (w[b] * ((S - Y[b]) ** 2).sum(1)).sum() / w[b].sum()
        if best is None or e < best[0]: best = (e, lam)
    return best[1]
class Ctx:
    def __init__(s, T, with_offset=True):
        s.T = T; s.frame, s.yc, s.xc = build_frame(cur_data(T), load_history(T - 1)); s.xs = shares_cols(s.xc); s.xl = [x[2:] for x in s.xs]; s.yl = [y[2:] for y in s.yc]
        s.ag = AGREEMENTS.get(T, []); fr = s.frame; vc = ["v_" + y[2:] for y in s.yc]; tv = fr[vc].sum().values; s.tsh = tv / tv.sum(); s.vc = vc
        s.ts = seats_of(dict(zip(s.yc, tv)), s.yc, s.ag); s.X = fr[s.xc].values; s.Xs = fr[s.xs].values; s.Y = fr[s.yc].values; s.w = fr.valid.values.astype(float)
        s.P0 = prior(T, s.xl, s.yl); s.lam = None
        if with_offset:
            try: s.lam = eb_lambda(T)
            except Exception as ex: print("eb_lambda failed", T, ex, file=sys.stderr)
        s.Wref = np.sort(s.w)[::-1][: max(1, len(fr) // 100)].sum() * 0 + s.w.mean() * (len(fr) // 100)
    def S(s, m, mask):
        c, u = mask, ~mask
        if m.startswith("base"):
            lam = {"base": 5.0, "base_l5e2": 5e2, "base_l5e3": 5e3, "base_l5e4": 5e4}[m]
            return ridge_fit_predict(s.X[c], s.Y[c], np.sqrt(s.w[c]), s.X[u], lam)
        if m in ("transfer", "transfer_const", "oracle_P"):
            if m == "oracle_P": P = fit_P(s.Xs, s.Y, s.w, s.P0, 0.0); Xu = s.Xs[u]
            else:
                kap = 0.02 if m == "transfer" else 0.02 * s.Wref / s.w[c].sum()
                P = fit_P(s.Xs[c], s.Y[c], s.w[c], s.P0, kap); Xu = s.Xs[u]
            S = Xu @ P; return S / np.clip(S.sum(1, keepdims=True), 1e-9, None)
        if m == "offset":
            return offset_S(s.X[c], s.Xs[c], s.Y[c], s.w[c], s.P0, s.X[u], s.Xs[u], s.lam)
    def score(s, S, mask):
        fr = s.frame; c, u = fr[mask], fr[~mask]; uv = u.prev_valid.values * (c.valid.sum() / c.prev_valid.sum())
        tot = c[s.vc].sum().values + (S * uv[:, None]).sum(0); sh = tot / tot.sum(); se = seats_of(dict(zip(s.yc, tot)), s.yc, s.ag)
        return 100 * np.abs(sh - s.tsh).mean(), sum(abs(se.get(k, 0) - s.ts.get(k, 0)) for k in set(se) | set(s.ts)) / 2
def orders3(ctx):
    fr = ctx.frame; n = len(fr); z = fr["x_מחל"].values; z = (z - z.mean()) / (z.std() + 1e-9)
    for b in BETAS:
        for seed in range(3):
            rng = np.random.default_rng(100 + seed); yield f"pl{b}", seed, np.argsort(b * z + rng.gumbel(size=n))
    rng = np.random.default_rng(0); yield "small_first", 0, np.argsort(fr.valid.values + rng.random(n)); yield "low_turnout_first", 0, np.argsort(fr.x_turn.values + 1e-6 * rng.random(n))
STACK = ("base", "transfer", "offset")
def one(T):
    ctx = Ctx(T); n = len(ctx.frame); rows = []; step = n / 100.0; models = ["base", "base_l5e2", "base_l5e3", "base_l5e4", "transfer", "transfer_const", "oracle_P", "offset"]
    if ctx.lam is None: models.remove("offset")
    stack_ok = ctx.lam is not None
    for on, seed, order in orders3(ctx):
        for f in FR:
            mask = np.zeros(n, bool); mask[order[:int(round(f * n))]] = True
            for m in models:
                a, b = ctx.score(ctx.S(m, mask), mask); rows.append(dict(T=T, order=on, seed=seed, frac=f, method=m, share_mae_pp=a, seats=b))
        if not stack_ok: continue
        Sall = {m: {} for m in STACK}; masks = {}
        for j in range(1, 41):
            mask = np.zeros(n, bool); mask[order[:int(round(j * step))]] = True; masks[j] = mask
            for m in STACK:
                Sf = np.full((n, len(ctx.yc)), np.nan); Sf[~mask] = ctx.S(m, mask); Sall[m][j] = Sf
        L = {m: [] for m in STACK}
        for j in range(2, 41):
            idx = order[int(round((j - 1) * step)):int(round(j * step))]; ww = ctx.w[idx]
            for m in STACK: L[m].append((ww * ((Sall[m][j - 1][idx] - ctx.Y[idx]) ** 2).sum(1)).sum() / ww.sum())
        eta = 1.0 / np.mean([np.mean(L[m][:3]) for m in STACK])
        for f in FR:
            j = int(round(f * 100)); k = j - 1  # scored batches 2..j -> L[0..j-2]
            if k >= 3: lw = np.array([-eta * np.sum(L[m][:k]) for m in STACK]); wts = np.exp(lw - lw.max()); wts /= wts.sum()
            else: wts = np.ones(3) / 3
            mask = masks[j]; S = sum(wt * Sall[m][j][~mask] for wt, m in zip(wts, STACK)); a, b = ctx.score(S, mask)
            rows.append(dict(T=T, order=on, seed=seed, frac=f, method="stack", share_mae_pp=a, seats=b))
    return pd.DataFrame(rows)
def merge():
    Ts = (20, 21, 23, 24, 25, 26); d = pd.concat([pd.read_csv(f"/tmp/round3_{T}.csv") for T in Ts if __import__("os").path.exists(f"/tmp/round3_{T}.csv")]); d.to_csv("results/round3.csv", index=False)
    d["set"] = np.where(d["T"] >= 23, "dev23-26", "holdout20-21"); pd.set_option("display.width", 250)
    for k in ("share_mae_pp", "seats"):
        print(k); print(d.groupby(["set", "order", "frac", "method"])[k].mean().unstack("method").round(3).to_string())
if __name__ == "__main__":
    merge() if sys.argv[1] == "merge" else one(int(sys.argv[1])).to_csv(f"/tmp/round3_{sys.argv[1]}.csv", index=False)
