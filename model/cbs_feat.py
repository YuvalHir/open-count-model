"""cbs-v1: CBS locality index as extra ridge features. See docs/prereg/cbs_v1.md"""
import sys, numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from .load import load_history, load_live, live_snapshots
from .project import build_frame, project
from .backtest import orders, seats_of, AGREEMENTS
def cbs():
    c = pd.read_csv("data-raw/cbs/cbs_index_2021.csv").drop_duplicates("loc_code")
    c["pop"] = pd.to_numeric(c.pop_2021.astype(str).str.replace(",", ""), errors="coerce"); return c.set_index("loc_code")
def one(T):
    cur = load_live(live_snapshots()[-1][1]) if T == 26 else load_history(T); frame, yc, xc = build_frame(cur, load_history(T - 1)); ag = AGREEMENTS.get(T, [])
    c = cbs(); idx = frame.loc_code.map(c.index_2021); pop = np.log(frame.loc_code.map(c["pop"]))
    w = frame.valid.values; 
    for nm, v in (("cbs_idx", idx), ("cbs_logpop", pop)):
        m = np.nansum(v.values * w) / w[v.notna().values].sum(); v = v.fillna(m); frame[nm] = (v - m) / (v.std() + 1e-9)
    xc2 = xc + ["cbs_idx", "cbs_logpop"]
    vc = ["v_" + y[2:] for y in yc]; tv = frame[vc].sum().values; tsh = tv / tv.sum(); ts = seats_of(dict(zip(yc, tv)), yc, ag); rows = []
    for seed in range(3):
        rng = np.random.default_rng(seed)
        for on, order in orders(frame, rng):
            if on not in ("random", "low_likud_first", "small_first", "low_turnout_first") or (on != "random" and seed): continue
            for f in (0.01, 0.05, 0.20, 0.40):
                mask = np.zeros(len(frame), bool); mask[order[:int(round(f * len(frame)))]] = True
                for mode, cols in (("base", xc), ("cbs", xc2)):
                    pr = project(frame, yc, cols, mask); pv = np.array(list(pr.values())); psh = pv / pv.sum(); s = seats_of(pr, yc, ag)
                    se = sum(abs(s.get(k, 0) - ts.get(k, 0)) for k in set(s) | set(ts)) / 2
                    rows.append(dict(T=T, order=on, seed=seed, frac=f, mode=mode, share_mae_pp=100 * np.abs(psh - tsh).mean(), seats=se))
    return pd.DataFrame(rows)
if __name__ == "__main__":
    if sys.argv[1] == "merge":
        d = pd.concat([pd.read_csv(f"/tmp/cbs_{T}.csv") for T in range(19, 27)]); d.to_csv("results/cbs_feat.csv", index=False)
        d["set"] = np.where(d["T"] >= 22, "dev22-26", "holdout19-21")
        g = d.groupby(["set", "order", "frac", "mode"]).share_mae_pp.mean().unstack("mode"); g["chg%"] = 100 * (g.cbs / g.base - 1); print(g.round(3).to_string())
    else:
        T = int(sys.argv[1]); one(T).to_csv(f"/tmp/cbs_{T}.csv", index=False)
