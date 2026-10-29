"""gp-gate-v1: GP noise grid and gate. See docs/prereg/gp_gate_v1.md"""
import sys, numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from .round3 import Ctx, orders3, FR
from .round4 import gp_S, gstat
NRS = (0.1, 0.5, 2.0)
def one(T):
    ctx = Ctx(T, with_offset=False); n = len(ctx.frame); rows = []; nulls = {}; rng = np.random.default_rng(7)
    for on, seed, order in orders3(ctx):
        for f in FR:
            mask = np.zeros(n, bool); mask[order[:int(round(f * n))]] = True; g, thr = gstat(ctx, mask, nulls)
            for nr in NRS:
                a, b = ctx.score(gp_S(ctx, mask, rng, nr), mask); rows.append(dict(T=T, order=on, seed=seed, frac=f, method=f"gp{nr}", share_mae_pp=a, seats=b, g=g, thr=thr))
    return pd.DataFrame(rows)
if __name__ == "__main__": one(int(sys.argv[1])).to_csv(f"/tmp/round5_{sys.argv[1]}.csv", index=False)
