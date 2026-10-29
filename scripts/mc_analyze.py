"""Aggregate mc-v1 draws. Prints summary and writes results/mc_summary.csv and results/mc_draws_agg.csv (per draw election-mean)."""
import pandas as pd, numpy as np, glob, sys
d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("/tmp/mc_[0-9]*.csv"))]); d["set"] = np.where(d["T"] >= 23, "dev", "hold")
# switch cutoff 5%: transfer if f<=0.05 and g>thr else base
k = ["T", "draw", "beta", "frac"]; w = d.pivot_table(index=k, columns="method", values=["share_mae_pp", "seats"]); g = d[d.method == "base"].set_index(k)[["g", "thr"]]
sw = pd.DataFrame(index=w.index)
for v in ("share_mae_pp", "seats"):
    use = (w.index.get_level_values("frac") <= 0.05) & (g.loc[w.index, "g"].values > g.loc[w.index, "thr"].values)
    sw[v] = np.where(use, w[(v, "transfer")], w[(v, "base")])
rows = []
for v in ("share_mae_pp", "seats"):
    for m in ("base", "transfer", "gp"): rows.append(w[v][m].rename("val").reset_index().assign(method=m, metric=v))
    rows.append(sw[v].rename("val").reset_index().assign(method="switch5", metric=v))
a = pd.concat(rows); a["set"] = np.where(a["T"] >= 23, "dev", "hold"); a["ndraw"] = 1
# election-mean per draw
dm = a.groupby(["set", "metric", "method", "beta", "frac", "draw"]).val.mean().reset_index(); dm.to_csv("results/mc_draws_agg.csv", index=False)
base = dm[dm.method == "base"].set_index(["set", "metric", "beta", "frac", "draw"]).val
out = []
for (st, me, m, b, f), x in dm.groupby(["set", "metric", "method", "beta", "frac"]):
    bb = base.loc[(st, me, b, f)].reindex(x.draw.values).values; v = x.val.values
    out.append(dict(set=st, metric=me, method=m, beta=b, frac=f, ndraws=len(v), mean=v.mean(), p5=np.percentile(v, 5), p95=np.percentile(v, 95), base_mean=bb.mean(), change_pct=100 * (v.mean() / bb.mean() - 1), win_rate=np.mean(v < bb)))
o = pd.DataFrame(out); o.to_csv("results/mc_summary.csv", index=False)
if __name__ == "__main__" and len(sys.argv) > 1:
    pd.set_option("display.width", 250); print(o[(o.metric == sys.argv[1])].round(3).to_string())
