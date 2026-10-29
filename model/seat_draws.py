"""ideas569-v1, idea 5: seat-level joint draws, threshold probabilities, calibration. See docs/prereg/ideas569_v1.md"""
import sys, numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from .load import load_history, load_live, live_snapshots
from .project import build_frame, project_draws
from .backtest import orders, seats_of, AGREEMENTS
SC = (1, 1.5, 2, 3, 4)
def run(T):
    cur = load_live(live_snapshots()[-1][1]) if T == 26 else load_history(T)
    frame, yc, xc = build_frame(cur, load_history(T - 1)); ag = AGREEMENTS.get(T, [])
    vc = ["v_" + y[2:] for y in yc]; tv = frame[vc].sum().values; ts = seats_of(dict(zip(yc, tv)), yc, ag)
    lists = [y[2:] for y in yc]; truth = np.array([ts.get(l, 0) for l in lists])
    rows = []
    rng = np.random.default_rng(0)
    for on, order in orders(frame, rng):
        if on not in ("random", "low_likud_first", "small_first"): continue
        for f in (0.05, 0.20):
            mask = np.zeros(len(frame), bool); mask[order[:int(round(f * len(frame)))]] = True
            dr = project_draws(frame, yc, xc, mask, n_draws=60, seed=1); med = np.median(dr, 0)
            for s in SC:
                d2 = med + s * (dr - med); d2 = np.clip(d2, 0, None)
                S = np.array([[seats_of(dict(zip(yc, row)), yc, ag).get(l, 0) for l in lists] for row in d2])
                lo, hi = np.percentile(S, [10, 90], axis=0); cov = ((truth >= lo) & (truth <= hi))
                pp = (S > 0).mean(0); br = (pp - (truth > 0)) ** 2
                rel = (lists_rel := np.array([(S[:, j] > 0).any() or truth[j] > 0 for j in range(len(lists))]))
                rows.append(dict(T=T, order=on, frac=f, s=s, coverage=cov[rel].mean(), width=(hi - lo)[rel].mean(), brier_pass=br[rel].mean()))
    return pd.DataFrame(rows)
def main():
    T = int(sys.argv[1]); run(T).to_csv(f"/tmp/seat_draws_{T}.csv", index=False)
def merge():
    d = pd.concat([pd.read_csv(f"/tmp/seat_draws_{T}.csv") for T in range(22, 27)]); d.to_csv("results/seat_draws.csv", index=False)
    print(d[d.s == 1].pivot_table(index=["order", "frac"], columns="T", values="coverage").round(2).to_string())
    ch = []
    for (o, f), g in d.groupby(["order", "frac"]):
        for T in range(22, 27):
            o_ = g[g["T"] != T].groupby("s").coverage.mean(); s = (o_ - 0.8).abs().idxmin()
            r = g[(g["T"] == T) & (g.s == s)].iloc[0]; r0 = g[(g["T"] == T) & (g.s == 1)].iloc[0]
            ch.append(dict(order=o, frac=f, T=T, s_chosen=s, cov_s1=r0.coverage, cov_chosen=r.coverage, brier_s1=r0.brier_pass, brier_chosen=r.brier_pass))
    c = pd.DataFrame(ch); c.to_csv("results/seat_draws_loo.csv", index=False); print(c.round(2).to_string())
if __name__ == "__main__":
    merge() if len(sys.argv) > 1 and sys.argv[1] == "merge" else main()
