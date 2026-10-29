"""Does the CEC per-box 20:00 turnout file help? K26 only (no such files exist for past elections that we found).
Two uses: (1) box size: predict a box's valid votes from voters@20 instead of last election's size;
(2) a feature: this election's turnout share of the box in the ridge model.
Evaluated on the K26 count so far, in simulated orders. K26 is NOT an independent holdout (development use)."""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from .load import load_history, load_live, live_snapshots, ROOT
from .project import build_frame, ridge_fit_predict
from .backtest import seats_of, AGREEMENTS

def load_turnout(h="20"):
    t = pd.read_excel(f"{ROOT}/data-raw/turnout/voter_turnout_{h}.xlsx").iloc[:, :8]
    t.columns = ["loc_code", "name", "station", "iron", "reg", "voters20", "pct", "t"]
    t = t[pd.to_numeric(t.loc_code, errors="coerce").notna()].copy()
    for c in ("loc_code", "station", "reg", "voters20"):
        t[c] = pd.to_numeric(t[c])
    return t[["loc_code", "station", "voters20"]]

def main():
    cur = load_live(live_snapshots()[-1][1]); prev = load_history(25)
    fr, yc, xc = build_frame(cur, prev)
    c0 = cur[~cur.is_envelope].copy(); c0["place"] = c0.station.astype(float).astype(int)
    v20 = c0.merge(load_turnout(), on=["loc_code", "station"], how="left").groupby(["loc_code", "place"]).voters20.sum().rename("v20").reset_index()
    fr = fr.assign(place=fr.station.astype(float).astype(int)).merge(v20, on=["loc_code", "place"], how="left")
    fr["v20"] = fr.v20.fillna(fr.prev_valid * fr.valid.sum() / fr.prev_valid.sum())
    fr["x_t20"] = fr.v20 / fr.registered
    vc = ["v_" + y[2:] for y in yc]; tv = fr[vc].sum().values; ts = seats_of(dict(zip(yc, tv)), yc, AGREEMENTS[26])
    rows = []
    def run(use_size, use_feat, order, f):
        m = np.zeros(len(fr), bool); m[order[:int(f * len(fr))]] = True
        c, u = fr[m], fr[~m]
        cols = xc + (["x_t20"] if use_feat else [])
        ratio = c.valid.sum() / (c.v20.sum() if use_size else c.prev_valid.sum())
        uv = (u.v20 if use_size else u.prev_valid).values * ratio
        P = ridge_fit_predict(c[cols].values, c[yc].values, np.sqrt(c.valid.values), u[cols].values, 5.0)
        votes = c[vc].sum().values + (P * uv[:, None]).sum(0)
        sh = votes / votes.sum()
        s = seats_of(dict(zip(yc, votes)), yc, AGREEMENTS[26])
        return 100 * np.abs(sh - tv / tv.sum()).mean(), sum(abs(s.get(k, 0) - ts.get(k, 0)) for k in set(s) | set(ts)) / 2
    for oname in ("random", "low_likud_first", "small_first"):
        for f in (0.02, 0.05, 0.10, 0.20):
            for cfg in ((0, 0), (1, 0), (0, 1), (1, 1)):
                r = []
                for seed in range(4 if oname == "random" else 1):
                    rng = np.random.default_rng(seed); n = len(fr)
                    order = rng.permutation(n) if oname == "random" else (np.argsort(fr["x_מחל"].values + 1e-6 * rng.random(n)) if oname == "low_likud_first" else np.argsort(fr.valid.values + rng.random(n)))
                    r.append(run(*cfg, order, f))
                rows.append(dict(order=oname, frac=f, size_from_turnout=cfg[0], turnout_feature=cfg[1], share_mae_pp=np.mean([x[0] for x in r]), seats=np.mean([x[1] for x in r])))
    d = pd.DataFrame(rows); d.to_csv("results/turnout_k26.csv", index=False)
    print(d.pivot_table(index=["order", "frac"], columns=["size_from_turnout", "turnout_feature"], values=["share_mae_pp", "seats"]).round(2).to_string())

if __name__ == "__main__":
    main()
