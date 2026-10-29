"""ideas569-v1, idea 9: rake_pg exit-poll estimator (past-vote rescaling inside each profile group). See docs/prereg/ideas569_v1.md"""
import sys, numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from .exitpoll import prepare, lie, pick, estimate, SCEN
from .backtest import AGREEMENTS, seats_of
def est_rake(D, idx, wt, m, rng, Q, Qx):
    C = rng.multinomial(m, Q[idx]) / m; Cx = rng.multinomial(m, Qx[idx]) / m; g = D["grp"]; sz = D["sz"]
    th = np.zeros(C.shape[1])
    for k in (0, 1, 2):
        pm = g == k
        if not pm.any(): continue
        pg = sz[pm].sum() / sz.sum(); Xg = (D["X"][pm] * sz[pm][:, None]).sum(0) / sz[pm].sum()
        sel = g[idx] == k
        if not sel.any(): th += pg * Xg; continue
        w = wt[sel]; rep = (Cx[sel] * w[:, None]).sum(0) / w.sum()
        f = np.clip(np.where(rep > 1e-4, Xg / np.clip(rep, 1e-4, None), 1.0), 0.5, 2.0)
        th += pg * (Xg + ((C[sel] * f - D["X"][idx][sel]) * w[:, None]).sum(0) / w.sum())
    th = np.clip(th, 0, None); return th / th.sum()
def run(T, reps=100):
    D = prepare(T); letters = D["letters"]; yc = ["y_" + l for l in letters]; ag = AGREEMENTS.get(T, [])
    shy = letters[int(np.argmax(D["truth"][:-1]))]; tseats = seats_of(dict(zip(yc, D["truth"] * 1e6)), yc, ag); rows = []
    for sc in ("none", "shy15", "hard_nr", "noise10_shy15"):
        Q = lie(D["S"], letters, sc, shy); Qx = lie(D["X"], letters, sc, shy)
        for n, m in ((60, 100), (120, 200)):
            for di, design in enumerate(("strat_prior", "strat_prior_pastvote", "rake_pg")):
                rng = np.random.default_rng([T, SCEN.index(sc), m, n, di]); err = []; sm = []
                for r in range(reps):
                    idx, wt = pick(D, "strat_prior" if design != "strat_prior_pastvote" else "strat_prior_pastvote", n, rng)
                    th = est_rake(D, idx, wt, m, rng, Q, Qx) if design == "rake_pg" else estimate(D, design, idx, wt, m, rng, Q, Qx)
                    s = seats_of(dict(zip(yc, th * 1e6)), yc, ag); err.append(np.abs(th - D["truth"]).mean())
                    sm.append(sum(abs(s.get(k, 0) - tseats.get(k, 0)) for k in set(s) | set(tseats)) / 2)
                rows.append(dict(T=T, scenario=sc, n=n, m=m, design=design, share_mae_pp=100 * np.mean(err), seats_oop=np.mean(sm)))
    return pd.DataFrame(rows)
if __name__ == "__main__":
    if sys.argv[1] == "merge":
        d = pd.concat([pd.read_csv(f"/tmp/rake_{T}.csv") for T in range(22, 27)]); d.to_csv("results/rake_exit.csv", index=False)
        print(d.groupby(["n", "scenario", "design"])[["share_mae_pp", "seats_oop"]].mean().round(3).unstack("design").to_string())
    else:
        T = int(sys.argv[1]); run(T).to_csv(f"/tmp/rake_{T}.csv", index=False)
