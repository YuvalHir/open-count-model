"""Matching voting places between election T-1 and T.

The CEC files carry no street address or coordinates, only (locality code, box number,
registered voters). Box numbers are renumbered between elections, so we test strategies:
  exact    : same (locality, place number)                         [baseline]
  guard    : exact, but reject the pair if registered voters differ a lot (ratio outside 0.6-1.67)
  assign   : within each locality, optimal one-to-one assignment on registered-voter size
             and number proximity (Hungarian), with a cap on the allowed size mismatch
  hybrid   : guarded exact matches first; the leftovers are assigned by size
  fill     : ALL exact matches kept; only the leftovers (no same-number place) are assigned by size
Returns for each current place the index of its matched previous place (or -1).
"""
import numpy as np
from scipy.optimize import linear_sum_assignment

def _pairs_exact(c, p):
    key = {(l, s): i for i, (l, s) in enumerate(zip(p.loc_code, p.station))}
    return np.array([key.get((l, s), -1) for l, s in zip(c.loc_code, c.station)])

def match(c, p, strategy="exact", ratio=1.67, num_w=0.02, cap=0.7):
    c = c.reset_index(drop=True); p = p.reset_index(drop=True)
    ex = _pairs_exact(c, p)
    if strategy == "exact":
        return ex
    if strategy == "fill":
        strategy, ratio = "hybrid", 1e9
    cr = c.registered.values.astype(float); pr = p.registered.values.astype(float)
    out = ex.copy()
    if strategy in ("guard", "hybrid"):
        for i, j in enumerate(ex):
            if j >= 0:
                r = cr[i] / max(pr[j], 1)
                if r > ratio or r < 1 / ratio:
                    out[i] = -1
    if strategy == "guard":
        return out
    used = set(out[out >= 0]) if strategy == "hybrid" else set()
    cg = c.groupby("loc_code").indices; pg = p.groupby("loc_code").indices
    for l, ci in cg.items():
        if l not in pg:
            continue
        ci = np.array([i for i in ci if out[i] < 0]) if strategy == "hybrid" else ci
        pi = np.array([j for j in pg[l] if j not in used])
        if len(ci) == 0 or len(pi) == 0:
            continue
        cost = np.abs(np.log(cr[ci][:, None] / np.maximum(pr[pi][None, :], 1)))
        cost = cost + num_w * np.abs(c.station.values[ci][:, None] - p.station.values[pi][None, :]) ** 0.5
        a, b = linear_sum_assignment(cost)
        for x, y in zip(a, b):
            if cost[x, y] <= cap:
                out[ci[x]] = pi[y]
    return out
