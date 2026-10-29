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

def _site_pass(c, p, out, used, cr, pr, cap=0.7):
    """Match places that stand in the same building (same address, then same name) by size within that building."""
    for key in (["s_addr", "s_name"], ["s_addr"], ["s_name"]):
        cg = c[(out < 0)].groupby(["loc_code"] + key).indices if False else None
        free_c = np.where(out < 0)[0]
        free_p = np.array([j for j in range(len(p)) if j not in used])
        if len(free_c) == 0 or len(free_p) == 0:
            break
        ck = c.iloc[free_c].groupby(["loc_code"] + key).indices
        pk = p.iloc[free_p].groupby(["loc_code"] + key).indices
        for k, ci in ck.items():
            if k not in pk:
                continue
            ci = free_c[ci]; pi = free_p[pk[k]]
            cost = np.abs(np.log(cr[ci][:, None] / np.maximum(pr[pi][None, :], 1)))
            cost = cost - 0.3 * (c.station.values[ci][:, None] == p.station.values[pi][None, :])
            a, b = linear_sum_assignment(cost)
            for x, y in zip(a, b):
                if cost[x, y] <= cap:
                    out[ci[x]] = pi[y]; used.add(pi[y])

def _split_pass(c, p, out, num_w=0.02, cap=0.5):
    """Leftover current places: a big previous place of size R is treated as k=round(R/s) equal parts (one-to-many splits)."""
    cr = c.registered.values.astype(float); pr = p.registered.values.astype(float)
    used = set(out[out >= 0]); cg = c.groupby("loc_code").indices; pg = p.groupby("loc_code").indices
    for l, ci in cg.items():
        if l not in pg: continue
        ci = np.array([i for i in ci if out[i] < 0]); pi = np.array([j for j in pg[l] if j not in used])
        if len(ci) == 0 or len(pi) == 0: continue
        s = max(float(np.median(cr[ci])), 1.0); ks = np.maximum(1, np.round(pr[pi] / s)).astype(int)
        cols = np.repeat(np.arange(len(pi)), ks); part = pr[pi][cols] / ks[cols]
        cost = np.abs(np.log(cr[ci][:, None] / np.maximum(part[None, :], 1)))
        cost = cost + num_w * np.abs(c.station.values[ci][:, None] - p.station.values[pi][cols][None, :]) ** 0.5
        a, b = linear_sum_assignment(cost)
        for x, y in zip(a, b):
            if cost[x, y] <= cap: out[ci[x]] = pi[cols[y]]
    return out

def match(c, p, strategy="exact", ratio=1.67, num_w=0.02, cap=0.7, reuse=None):
    c = c.reset_index(drop=True); p = p.reset_index(drop=True)
    if strategy == "split":
        return _split_pass(c, p, match(c, p, "fill"))
    if strategy in ("site", "site2"):
        reuse = strategy == "site2"
        out = np.full(len(c), -1); used = set()
        cr = c.registered.values.astype(float); pr = p.registered.values.astype(float)
        if "s_addr" in c and "s_addr" in p:
            _site_pass(c, p, out, used, cr, pr)
        if "s_addr" in c and "s_name" in p and reuse:
            for key in (["s_addr", "s_name"], ["s_addr"], ["s_name"]):
                pk = p.groupby(["loc_code"] + key).indices
                for i in np.where(out < 0)[0]:
                    k = tuple(c.iloc[i][["loc_code"] + key])
                    if len(key) == 1: k = tuple(k)
                    if k in pk:
                        pi = pk[k]; dd = np.abs(np.log(cr[i] / np.maximum(pr[pi], 1)))
                        if dd.min() <= 1.0:   # within a factor of ~2.7 in registered voters
                            out[i] = pi[np.argmin(dd)]
        ex = _pairs_exact(c, p)
        for i, j in enumerate(ex):
            if out[i] < 0 and j >= 0 and j not in used:
                out[i] = j; used.add(j)
        cg = c.groupby("loc_code").indices; pg = p.groupby("loc_code").indices
        for l, ci in cg.items():
            if l not in pg:
                continue
            ci = np.array([i for i in ci if out[i] < 0]); pi = np.array([j for j in pg[l] if j not in used])
            if len(ci) == 0 or len(pi) == 0:
                continue
            cost = np.abs(np.log(cr[ci][:, None] / np.maximum(pr[pi][None, :], 1)))
            cost = cost + num_w * np.abs(c.station.values[ci][:, None] - p.station.values[pi][None, :]) ** 0.5
            a, b = linear_sum_assignment(cost)
            for x, y in zip(a, b):
                if cost[x, y] <= cap:
                    out[ci[x]] = pi[y]
        return out
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
