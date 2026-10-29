"""Bloc-level backtest (Knesset 22-25, final results as truth; simulated arrival orders).

Blocs (a simple, stated convention - lists are assigned by letter, Yisrael Beiteinu counts as 'rest'):
  right = Likud + Shas + UTJ + lists to the right of Likud (Yamina / Religious Zionism / Otzma)
  arab  = Joint List / Ra'am / Hadash-Ta'al lists
  rest  = every other list (centre, left, Yisrael Beiteinu, New Hope, ...)
Metrics per replay: mean absolute bloc-seat error over the 3 blocs; right-bloc seat error;
whether the projection puts 'right' on the correct side of 61 seats; whether the projection
picks the same bigger bloc out of right vs rest as the truth.
    python -m model.bloc_backtest -> results/bloc_backtest.csv
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from .load import load_history
from .project import build_frame, project, raw_projection
from .backtest import orders, seats_of, AGREEMENTS, FRACS

RIGHT = {22: {"מחל", "שס", "ג", "טב"}, 23: {"מחל", "שס", "ג", "טב"}, 24: {"מחל", "שס", "ג", "ט", "ב"}, 25: {"מחל", "שס", "ג", "ט"}}
ARAB = {22: {"ודעם"}, 23: {"ודעם"}, 24: {"ודעם", "עם"}, 25: {"עם", "ום"}}

def blocs(seats, T):
    r = sum(v for k, v in seats.items() if k in RIGHT[T]); a = sum(v for k, v in seats.items() if k in ARAB[T])
    return dict(right=r, arab=a, rest=sum(seats.values()) - r - a)

def run(T, seeds=3):
    frame, yc, xc = build_frame(load_history(T), load_history(T - 1))
    ag = AGREEMENTS.get(T, [])
    vcols = ["v_" + y[2:] for y in yc]
    tb = blocs(seats_of(dict(zip(yc, frame[vcols].sum().values)), yc, ag), T)
    rows = []
    for seed in range(seeds):
        rng = np.random.default_rng(seed)
        for oname, order in orders(frame, rng):
            if oname != "random" and seed > 0: continue
            for f in FRACS:
                m = np.zeros(len(frame), bool); m[order[:int(round(f * len(frame)))]] = True
                for method, pr in (("ridge", project(frame, yc, xc, m, 5.0)), ("raw_counted", raw_projection(frame, yc, m))):
                    pb = blocs(seats_of(pr, yc, ag), T)
                    err = {k: abs(pb[k] - tb[k]) for k in tb}
                    rows.append(dict(T=T, order=oname, seed=seed, frac=f, method=method,
                                     mae_bloc=np.mean(list(err.values())), err_right=err["right"], err_arab=err["arab"], err_rest=err["rest"],
                                     side61=bool((pb["right"] >= 61) == (tb["right"] >= 61)),
                                     bigger=bool((pb["right"] > pb["rest"]) == (tb["right"] > tb["rest"]))))
    return pd.DataFrame(rows), tb

if __name__ == "__main__":
    out = []
    for T in (22, 23, 24, 25):
        d, tb = run(T); out.append(d); print(T, "true blocs", tb)
    r = pd.concat(out); r.to_csv("results/bloc_backtest.csv", index=False)
    for o in ("random", "low_likud_first"):
        print(o); print(r[r.order == o].groupby(["method", "frac"])[["mae_bloc", "err_right", "side61", "bigger"]].mean().round(2).unstack(0).to_string())
