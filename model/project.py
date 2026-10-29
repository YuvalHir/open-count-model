"""Station-level projection: predict uncounted stations from counted ones.

Idea: for election T, each station has a result in election T-1. Fit, on the stations
counted so far, a ridge regression of each T list's vote share on the station's T-1 list
shares (+ turnout, size). This learns vote transfers between old and new lists without any
hand-made party mapping. Apply it to uncounted stations, sum, and allocate seats.
"""
import numpy as np
import pandas as pd
from .load import party_cols, to_places

MIN_SHARE_X = 0.005   # T-1 lists below this national share are pooled as "other"
MIN_SHARE_Y = 0.003   # T lists below this national share are pooled as "other"

def regular(df):
    return df[(~df.is_envelope) & (df.valid > 0) & (df.registered > 0)].copy()

def build_frame(cur: pd.DataFrame, prev: pd.DataFrame):
    cur, prev = to_places(cur), to_places(prev)
    """Return (frame, ycols, xcols). One row per regular station of `cur` with T-1 features.
    Unmatched stations get their locality's T-1 profile, or the national one."""
    pc_c, pc_p = party_cols(cur), party_cols(prev)
    cur, prev = regular(cur), regular(prev)
    # T-1 features
    tot_p = prev[pc_p].sum().sum()
    xl = [c for c in pc_p if prev[c].sum() / tot_p >= MIN_SHARE_X]
    px = prev[xl].div(prev.valid, axis=0)
    px["x_other"] = 1 - px.sum(axis=1)
    px.columns = ["x_" + c if not c.startswith("x_") else c for c in px.columns]
    prev_f = pd.concat([prev[["loc_code", "station", "registered", "voters", "valid"]].reset_index(drop=True),
                        px.reset_index(drop=True)], axis=1)
    prev_f["x_turn"] = prev_f.voters / prev_f.registered
    prev_f["x_logreg"] = np.log(prev_f.registered)
    xcols = [c for c in prev_f.columns if c.startswith("x_")]
    # locality and national fallbacks (valid-weighted)
    w = prev_f.valid.values[:, None]
    loc = (prev_f[xcols] * w).groupby(prev_f.loc_code).sum() / prev_f.groupby("loc_code").valid.sum().values[:, None]
    nat = (prev_f[xcols] * w).sum() / prev_f.valid.sum()
    f = cur[["loc_code", "loc_name", "station", "registered", "voters", "invalid", "valid"]].reset_index(drop=True).copy()
    cur_r = cur.reset_index(drop=True)
    pcols = xcols + ["valid"]
    # match voting places by (locality, place number); otherwise fall back to the locality profile
    b = prev_f.drop_duplicates(["loc_code", "station"]).set_index(["loc_code", "station"])[pcols]
    m = f.join(b.rename(columns={"valid": "prev_valid"}), on=["loc_code", "station"])
    m["matched"] = m.prev_valid.notna()
    um = ~m.matched
    for c in xcols:
        fill = m.loc_code.map(loc[c]) if True else None
        m.loc[um, c] = fill[um]
    for c in xcols:
        m[c] = m[c].fillna(nat[c])
    # y: shares of T lists
    tot_c = cur_r[pc_c].sum().sum()
    yl = [c for c in pc_c if cur_r[c].sum() / tot_c >= MIN_SHARE_Y]
    for c in yl:
        m["y_" + c] = (cur_r[c] / cur_r.valid).values
    m["y_other"] = 1 - m[["y_" + c for c in yl]].sum(axis=1)
    ycols = ["y_" + c for c in yl] + ["y_other"]
    for c in yl:
        m["v_" + c] = cur_r[c].values
    m["v_other"] = m.valid - m[["v_" + c for c in yl]].sum(axis=1)
    m["prev_valid"] = m.prev_valid.fillna(m.valid.mean())
    return m.reset_index(drop=True), ycols, xcols

def ridge_fit_predict(Xtr, Ytr, wtr, Xte, lam=5.0):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
    A = (Xtr - mu) / sd; B = (Xte - mu) / sd
    A1 = np.hstack([np.ones((len(A), 1)), A]); B1 = np.hstack([np.ones((len(B), 1)), B])
    W = wtr[:, None]
    R = lam * np.eye(A1.shape[1]); R[0, 0] = 0
    beta = np.linalg.solve(A1.T @ (A1 * W) + R, A1.T @ (Ytr * W))
    P = np.clip(B1 @ beta, 0, None)
    return P / np.clip(P.sum(1, keepdims=True), 1e-9, None)

def project(frame, ycols, xcols, counted_mask, lam=5.0):
    """Return projected total votes per y-list = counted votes + predicted uncounted votes."""
    c = frame[counted_mask]; u = frame[~counted_mask]
    vcols = ["v_" + y[2:] for y in ycols]
    counted_votes = c[vcols].sum().values
    if len(u) == 0:
        return dict(zip(ycols, counted_votes))
    ratio = c.valid.sum() / c.prev_valid.sum()           # global growth in valid votes
    u_valid = u.prev_valid.values * ratio
    P = ridge_fit_predict(c[xcols].values, c[ycols].values, np.sqrt(c.valid.values), u[xcols].values, lam)
    pred = (P * u_valid[:, None]).sum(0)
    return dict(zip(ycols, counted_votes + pred))

def raw_projection(frame, ycols, counted_mask):
    """Baseline: assume uncounted stations look like counted ones (shares from counted only)."""
    vcols = ["v_" + y[2:] for y in ycols]
    return dict(zip(ycols, frame[counted_mask][vcols].sum().values))
