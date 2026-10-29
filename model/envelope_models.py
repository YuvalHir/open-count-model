"""ideas569-v1, idea 6: envelope share models. See docs/prereg/ideas569_v1.md"""
import numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from .load import load_history, load_live, live_snapshots, party_cols
from .backtest import seats_of, AGREEMENTS
def data(T):
    return load_live(live_snapshots()[-1][1]) if T == 26 else load_history(T)
def sh(d, env):
    pc = party_cols(d); x = d[d.is_envelope == env]; return x[pc].sum(), x.valid.sum()
def main():
    D = {T: data(T) for T in range(22, 27)}
    S = {T: (sh(D[T], True), sh(D[T], False)) for T in D}
    rows = []
    for scheme in ("past_only", "loo"):
        for T in range(22, 27):
            hist = [k for k in D if k < T] if scheme == "past_only" else [k for k in D if k != T]
            if not hist: continue
            (ev, en), (rv, rn) = S[T]
            lists = ev.index; e = ev / en; r = rv / rn
            gaps = pd.concat([(S[k][0][0] / S[k][0][1] - S[k][1][0] / S[k][1][1]) for k in hist], axis=1).mean(axis=1, skipna=True)
            rat = pd.concat([((S[k][0][0] / S[k][0][1]) / (S[k][1][0] / S[k][1][1]).replace(0, np.nan)).replace([np.inf], np.nan) for k in hist], axis=1).mean(axis=1, skipna=True)
            est = {"naive": r, "additive": (r + gaps.reindex(lists).fillna(0)).clip(lower=0), "ratio": (r * rat.reindex(lists).fillna(1)).clip(lower=0)}
            ag = AGREEMENTS.get(T, []); yc = ["y_" + l for l in lists]
            def seats(v): return seats_of(dict(zip(yc, np.asarray(v, float))), yc, ag)
            tseats = seats((rv + ev).values)
            for k, v in est.items():
                v = v / v.sum(); s = seats((rv + v * en).values); keys = set(s) | set(tseats)
                rows.append(dict(scheme=scheme, T=T, model=k, mae_pp=100 * float((v - e).abs().mean()), seats=sum(abs(s.get(q, 0) - tseats.get(q, 0)) for q in keys) / 2))
    d = pd.DataFrame(rows); d.to_csv("results/envelope_models.csv", index=False)
    print(d.pivot_table(index=["scheme", "T"], columns="model", values="mae_pp").round(3).to_string())
    print(d.pivot_table(index=["scheme", "T"], columns="model", values="seats").to_string())
    print(d.groupby(["scheme", "model"])[["mae_pp", "seats"]].mean().round(3).to_string())
if __name__ == "__main__": main()
