"""round4-v1: blocked-CV blend (idea 4), GP residual (idea 6), prequential intervals (idea 5), bias meter. See docs/prereg/round4_v1.md"""
import sys, os, numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from .round3 import Ctx, orders3, FR
from .project import project_draws
def pc1(ctx):
    X = ctx.X; Z = (X - X.mean(0)) / (X.std(0) + 1e-9); u, s, vt = np.linalg.svd(Z[:: max(1, len(Z) // 2000)], full_matrices=False); return Z @ vt[0]
def blend_S(ctx, mask, p1):
    ids = np.where(mask)[0]; ids = ids[np.argsort(p1[ids])]; blocks = np.array_split(ids, 5); L = {"base": [], "transfer_const": []}
    for b in blocks:
        m2 = mask.copy(); m2[b] = False
        for m in L:
            S = ctx.S(m, m2)[np.searchsorted(np.where(~m2)[0], b)]; w = ctx.w[b]; L[m].append((w * ((S - ctx.Y[b]) ** 2).sum(1)).sum() / w.sum())
    Lm = {m: np.mean(v) for m, v in L.items()}; eta = 1.0 / np.mean(list(Lm.values())); lw = np.array([-eta * Lm["base"], -eta * Lm["transfer_const"]]); wt = np.exp(lw - lw.max()); wt /= wt.sum()
    return wt[0] * ctx.S("base", mask) + wt[1] * ctx.S("transfer_const", mask), wt[1]
def gp_S(ctx, mask, rng, nr=0.5):
    c, u = mask, ~mask; S0c = ctx.S("transfer_const", c)
    from .round2 import fit_P
    kap = 0.02 * ctx.Wref / ctx.w[c].sum(); P = fit_P(ctx.Xs[c], ctx.Y[c], ctx.w[c], ctx.P0, kap)
    Mc = ctx.Xs[c] @ P; Mc = Mc / np.clip(Mc.sum(1, keepdims=True), 1e-9, None); Mu = ctx.Xs[u] @ P; Mu = Mu / np.clip(Mu.sum(1, keepdims=True), 1e-9, None)
    mu, sd = ctx.X[c].mean(0), ctx.X[c].std(0) + 1e-9; A = (ctx.X[c] - mu) / sd; B = (ctx.X[u] - mu) / sd
    sub = A[rng.choice(len(A), min(400, len(A)), replace=False)]; d = np.sqrt(((sub[:, None] - sub[None]) ** 2).sum(-1)); ls = np.median(d[d > 0])
    k = lambda a, b: np.exp(-((a ** 2).sum(1)[:, None] + (b ** 2).sum(1)[None] - 2 * a @ b.T) / (2 * ls ** 2))
    wn = ctx.w[c] / ctx.w[c].mean(); Kcc = k(A, A) + nr * np.diag(1.0 / wn); alpha = np.linalg.solve(Kcc, ctx.Y[c] - Mc)
    S = np.clip(Mu + k(B, A) @ alpha, 0, None); return S / np.clip(S.sum(1, keepdims=True), 1e-9, None)
def gstat(ctx, mask, nulls):
    Xs = ctx.Xs; wp = ctx.frame.prev_valid.values.astype(float); tot = (Xs * wp[:, None]).sum(0) / wp.sum()
    G = lambda m: 100 * np.abs((Xs[m] * wp[m, None]).sum(0) / wp[m].sum() - tot).sum(); n = int(mask.sum())
    if n not in nulls:
        r2 = np.random.default_rng(12345); nulls[n] = np.percentile([G(np.isin(np.arange(len(mask)), r2.choice(len(mask), n, replace=False))) for _ in range(200)], 95)
    return G(mask), nulls[n]
def one(T):
    ctx = Ctx(T, with_offset=False); n = len(ctx.frame); p1 = pc1(ctx); rows, irows, nulls = [], [], {}; step = n / 100.0; rng = np.random.default_rng(7)
    for on, seed, order in orders3(ctx):
        qi = on in ("pl0", "pl4", "pl8")
        if qi:
            Sb = {}; E = []  # prequential errors of base per batch
            for j in range(1, 41):
                mask = np.zeros(n, bool); mask[order[:int(round(j * step))]] = True; Sb[j] = (mask, ctx.S("base", mask))
            for j in range(2, 41):
                mprev, S = Sb[j - 1]; idx = order[int(round((j - 1) * step)):int(round(j * step))]; w = ctx.w[idx]
                un = np.where(~mprev)[0]; pos = np.searchsorted(un, idx); uv = ctx.frame.prev_valid.values[idx] * (ctx.frame.valid.values[mprev].sum() / ctx.frame.prev_valid.values[mprev].sum())
                pred = (S[pos] * uv[:, None]).sum(0); pred = pred / pred.sum(); real = (ctx.Y[idx] * w[:, None]).sum(0) / w.sum(); E.append(pred - real)
            E = np.array(E)
        for f in FR:
            mask = np.zeros(n, bool); mask[order[:int(round(f * n))]] = True
            g, thr = gstat(ctx, mask, nulls); rows.append(dict(T=T, order=on, seed=seed, frac=f, method="_g", share_mae_pp=g, seats=thr))
            for m, fn in (("blockcv", lambda: blend_S(ctx, mask, p1)[0]), ("gp", lambda: gp_S(ctx, mask, rng))):
                a, b = ctx.score(fn(), mask); rows.append(dict(T=T, order=on, seed=seed, frac=f, method=m, share_mae_pp=a, seats=b))
            if qi:
                j = int(round(f * 100)); fr = ctx.frame; c = fr[mask]; uvot = fr.prev_valid.values[~mask] * (c.valid.sum() / c.prev_valid.sum()); tot_u = uvot.sum()
                cv = c[ctx.vc].sum().values; S = ctx.S("base", mask); pt = cv + (S * uvot[:, None]).sum(0); psh = pt / pt.sum(); u = tot_u / pt.sum()
                s = u * np.sqrt((E[: j - 1] ** 2).mean(0)) if j >= 2 else np.full(len(psh), np.nan)
                lo, hi = psh - 1.2816 * s, psh + 1.2816 * s; cov = np.mean((ctx.tsh >= lo) & (ctx.tsh <= hi)); wid = 100 * np.mean(hi - lo)
                dr = project_draws(fr, ctx.yc, ctx.xc, mask, n_draws=30, seed=seed); dsh = dr / dr.sum(1, keepdims=True); blo, bhi = np.percentile(dsh, 10, 0), np.percentile(dsh, 90, 0)
                bcov = np.mean((ctx.tsh >= blo) & (ctx.tsh <= bhi)); bw = 100 * np.mean(bhi - blo)
                irows.append(dict(T=T, order=on, seed=seed, frac=f, cov_preq=cov, width_preq_pp=wid, cov_boot=bcov, width_boot_pp=bw))
    pd.DataFrame(irows).to_csv(f"/tmp/round4i_{T}.csv", index=False); return pd.DataFrame(rows)
if __name__ == "__main__":
    one(int(sys.argv[1])).to_csv(f"/tmp/round4_{sys.argv[1]}.csv", index=False)
