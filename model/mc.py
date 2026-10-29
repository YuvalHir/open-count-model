"""mc-v1: Monte Carlo replication of transfer, GP, switch-cutoff-5% over many new arrival-order draws. See docs/prereg/mc_v1.md"""
import sys, time, numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from .round3 import Ctx
from .round4 import gp_S, gstat
BETAS = (0, 2, 4, 8); FRS = (0.01, 0.05, 0.20); S0 = 1000
def one(T, n_draws, out):
    ctx = Ctx(T, with_offset=False); n = len(ctx.frame); z = ctx.frame["x_מחל"].values; z = (z - z.mean()) / (z.std() + 1e-9); rows = []; nulls = {}; rng = np.random.default_rng(99); t0 = time.time()
    for d in range(n_draws):
        for b in BETAS:
            order = np.argsort(b * z + np.random.default_rng(S0 + d).gumbel(size=n) if True else 0)
            for f in FRS:
                mask = np.zeros(n, bool); mask[order[:int(round(f * n))]] = True; g, thr = gstat(ctx, mask, nulls); r = {}
                r["base"] = ctx.score(ctx.S("base", mask), mask); r["transfer"] = ctx.score(ctx.S("transfer", mask), mask); r["gp"] = ctx.score(gp_S(ctx, mask, rng), mask)
                for m, (a, s) in r.items(): rows.append(dict(T=T, draw=d, beta=b, frac=f, method=m, share_mae_pp=a, seats=s, g=g, thr=thr))
        if d == 0: print("first draw s", time.time() - t0, flush=True)
        if d % 10 == 9: pd.DataFrame(rows).to_csv(out, index=False)
    pd.DataFrame(rows).to_csv(out, index=False)
if __name__ == "__main__": one(int(sys.argv[1]), int(sys.argv[2]), f"/tmp/mc_{sys.argv[1]}.csv")
