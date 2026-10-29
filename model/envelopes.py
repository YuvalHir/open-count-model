"""External-envelope ("double envelope") votes: soldiers, hospitals, prisoners, diplomats, etc.

They are counted after the regular boxes and lean differently. v1 estimate of their list shares:
regular-box shares of this election plus the mean historical difference (envelope minus regular,
in share points) of the same list letter in earlier elections. Lists without history get 0 adjustment.
Total envelope votes: ratio to regular valid votes from earlier elections (6.3-9.6% of all valid).
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from .load import load_history, party_cols

def shares(df, envelope):
    pc = party_cols(df); d = df[df.is_envelope == envelope]
    return d[pc].sum() / d.valid.sum(), d.valid.sum()

def history_diff(ks):
    diffs = []
    for k in ks:
        d = load_history(k); e, _ = shares(d, True); r, _ = shares(d, False)
        diffs.append((e - r))
    return pd.concat(diffs, axis=1).mean(axis=1, skipna=True)   # per letter, mean over elections where present

def estimate(regular_shares: pd.Series, diff: pd.Series) -> pd.Series:
    adj = regular_shares + diff.reindex(regular_shares.index).fillna(0)
    adj = adj.clip(lower=0)
    return adj / adj.sum()

def backtest(T=25, prior=(22, 23, 24)):
    d = load_history(T); e, ne = shares(d, True); r, nr = shares(d, False)
    diff = history_diff(prior)
    est = estimate(r, diff)
    top = e.sort_values(ascending=False).index[:10]
    out = pd.DataFrame({"true_env_pct": 100 * e[top], "naive_regular_pct": 100 * r[top], "estimate_pct": 100 * est[top]}).round(1)
    mae_naive = 100 * float((e - r).abs().mean()); mae_est = 100 * float((e - est).abs().mean())
    return out, mae_naive, mae_est, ne / nr

if __name__ == "__main__":
    out, a, b, ratio = backtest()
    print(out.to_string())
    print(f"MAE over all lists (share points): naive {a:.3f}, with historical envelope lean {b:.3f}")
    print("envelope/regular valid ratio K25: %.3f" % ratio)
