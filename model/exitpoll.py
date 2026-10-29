"""Exit-poll sampling-design simulation (modelling of sampling error only).

Question: if a poll interviews m voters leaving each of n polling places, how well can the national
vote shares and the 120 seats be recovered, which places should be picked, how much do respondents who
give a wrong answer matter, and how few places are enough?

What is real here: the true vote of every voting place in K22-25 (CEC results) and its profile in the
previous election (matching as in model.project). What is assumed: how many respondents give a wrong
answer and in which direction (scenarios below). Those are assumptions, not measurements.

Nothing is tuned on outcomes: the designs and scenarios are fixed up front, so K22-25 are effectively
held-out for the design comparison (no leave-one-out needed). The set of designs was chosen before looking
at results. K26 uses the current live count (envelopes missing) and is provisional.

Selection and weighting use only information available before election day (registered voters x previous turnout);
the truth is the actual share of valid votes in regular boxes (envelopes are not part of any box sample).
Unit = voting place (sub-boxes of one building merged), the same unit the rest of the model uses.
"""
import os, sys, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
from .load import load_history, load_live, live_snapshots
from .project import build_frame
from .backtest import AGREEMENTS, seats_of

NS = [10, 15, 20, 30, 40, 50, 60, 80, 100, 150]
DESIGNS = ["srs_ratio", "pps_ratio", "strat_ratio", "strat_prior", "strat_prior_pastvote",
           "strat_prior_ps", "strat_prior_bk", "strat_ridge", "strat_greg", "strat_greg_ps_bk"]
SCEN = ["none", "noise10", "shy15", "refuse20", "noise10_shy15", "hard_nr", "place_refuse", "hard_both"]
HAREDI = {"ג", "שס"}; ARAB = {"ודעם", "עם", "ד", "ום", "ודם"}   # list letters, K22-26
PLACE_REFUSE = 0.5   # assumed: share of Haredi-/Arab-profile places that do not let interviewers in
M_BASE = 100

def prepare(T):
    cur = load_live(live_snapshots()[-1][1]) if T == 26 else load_history(T)
    frame, yc, xc = build_frame(cur, load_history(T - 1))
    frame = frame[frame.valid > 0].reset_index(drop=True)
    letters = [y[2:] for y in yc]
    S = np.clip(frame[yc].values, 0, 1); S = S / S.sum(1, keepdims=True)
    w = frame.valid.values.astype(float)
    # prior profile aligned to the y columns (letters absent in the earlier election get 0; rest goes to other)
    X = np.zeros_like(S)
    for j, l in enumerate(letters):
        if l != "other" and "x_" + l in frame:
            X[:, j] = frame["x_" + l].values
    X[:, -1] = np.clip(1 - X[:, :-1].sum(1), 0, 1)
    X = X / X.sum(1, keepdims=True)
    # order for implicit stratification: first principal component of the prior profile (no outcome used)
    Z = frame[[c for c in xc if c != "x_logreg"]].values
    Z = (Z - Z.mean(0)) / (Z.std(0) + 1e-9)
    pc1 = np.linalg.svd(Z, full_matrices=False)[2][0]
    order = np.argsort(Z @ pc1)
    truth = (S * w[:, None]).sum(0) / w.sum()
    hs = sum(X[:, j] for j, l in enumerate(letters) if l in HAREDI)
    ar = sum(X[:, j] for j, l in enumerate(letters) if l in ARAB)
    grp = np.where(hs > 0.5, 1, np.where(ar > 0.5, 2, 0))   # profile-based groups from the PREVIOUS election: 0 other, 1 Haredi-profile, 2 Arab-profile
    F = frame[xc].values.astype(float)
    # size known BEFORE election day: registered voters x last election's turnout (not the actual valid votes)
    sz = (frame.registered * frame.x_turn.clip(0.2, 1.0)).values.astype(float)
    return dict(T=T, frame=frame, letters=letters, S=S, X=X, w=w, sz=sz, order=order, truth=truth, grp=grp, F=F)

def lie(P, letters, scen, shy):
    """Reported-answer probabilities given true-vote probabilities P (rows = places). Assumed behaviour."""
    P = P.copy(); j = letters.index(shy); K = P.shape[1]
    if scen in ("noise10", "noise10_shy15"):      # 10% answer at random among the named lists
        u = np.ones(K); u[-1] = 0; u /= u.sum()
        P = 0.9 * P + 0.1 * u
    if scen in ("shy15", "noise10_shy15"):        # 15% of the largest list's voters name another list
        moved = 0.15 * P[:, j]; rest = P.copy(); rest[:, j] = 0
        rest = rest / np.clip(rest.sum(1, keepdims=True), 1e-12, None)
        P[:, j] -= moved; P += moved[:, None] * rest
    if scen == "refuse20":                        # the largest list's voters answer 20% less often
        P[:, j] *= 0.8
    if scen in ("hard_nr", "hard_both"):          # Haredi-list voters answer half as often, Arab-list voters 40% less often
        for k, l in enumerate(letters):
            if l in HAREDI: P[:, k] *= 0.5
            elif l in ARAB: P[:, k] *= 0.6
    return P / P.sum(1, keepdims=True)

def pick(D, design, n, rng):
    N = len(D["w"]); w = D["sz"]
    if design.startswith("srs"):
        idx = rng.choice(N, n, replace=False)
        return idx, w[idx]
    if design.startswith("pps"):
        perm = rng.permutation(N)
        cum = np.cumsum(w[perm]); step = cum[-1] / n
        pts = rng.random() * step + step * np.arange(n)
        return perm[np.searchsorted(cum, pts)], np.ones(n)
    o = D["order"]; cum = np.cumsum(w[o]); step = cum[-1] / n   # strat_*: systematic PPS along the prior-profile order
    pts = rng.random() * step + step * np.arange(n)
    return o[np.searchsorted(cum, pts)], np.ones(n)

def estimate(D, design, idx, wt, m, rng, Q, Qx):
    K = D["S"].shape[1]
    C = rng.multinomial(m, Q[idx]) / m                    # reported shares in each sampled place
    th = (C * wt[:, None]).sum(0) / wt.sum()
    if design.endswith("ratio"):
        return th
    Xbar = (D["X"] * D["sz"][:, None]).sum(0) / D["sz"].sum()     # full-population prior profile (known)
    if design in ("strat_prior_ps", "strat_greg_ps_bk", "strat_greg", "strat_ridge"):
        return _model_est(D, design, idx, wt, C, Xbar)
    if design in ("strat_prior", "strat_prior_bk"):
        th = Xbar + ((C - D["X"][idx]) * wt[:, None]).sum(0) / wt.sum()
    else:                                                  # also ask "how did you vote last time" and rescale
        Cx = rng.multinomial(m, Qx[idx]) / m
        rep = (Cx * wt[:, None]).sum(0) / wt.sum()
        f = np.where(rep > 1e-4, Xbar / np.clip(rep, 1e-4, None), 1.0)
        f = np.clip(f, 0.5, 2.0)
        th = Xbar + ((C * f - D["X"][idx]) * wt[:, None]).sum(0) / wt.sum()
    th = np.clip(th, 0, None)
    return th / th.sum()

def _model_est(D, design, idx, wt, C, Xbar):
    """Model-assisted estimators. ps = post-stratified on the profile groups (population sizes known beforehand)."""
    sz, grp = D["sz"], D["grp"]
    if design == "strat_prior_ps":
        Pall = D["X"]
    else:   # ridge of the reported shares on the previous-election profile of the sampled places (same ridge as the count model)
        from .project import ridge_fit_predict
        Pall = ridge_fit_predict(D["F"][idx], C, np.sqrt(wt), D["F"], 5.0)
        if design == "strat_ridge":
            th = (Pall * sz[:, None]).sum(0) / sz.sum()
            return th / th.sum()
    res = C - Pall[idx]
    if design == "strat_greg":
        th = (Pall * sz[:, None]).sum(0) / sz.sum() + (res * wt[:, None]).sum(0) / wt.sum()
    else:
        th = np.zeros(C.shape[1])
        for g in (0, 1, 2):
            m_ = grp == g
            if not m_.any(): continue
            pg = sz[m_].sum() / sz.sum()
            base = (Pall[m_] * sz[m_][:, None]).sum(0) / sz[m_].sum()
            sel = grp[idx] == g
            corr = (res[sel] * wt[sel][:, None]).sum(0) / wt[sel].sum() if sel.any() else 0
            th += pg * (base + corr)
    th = np.clip(th, 0, None)
    return th / th.sum()

def _refuse(D, idx, wt, design, scen, rng):
    """Some Haredi-/Arab-profile places turn the interviewers away (assumption). _bk designs try the neighbours
    in the profile order instead; the others simply lose the place."""
    g = D["grp"]
    if design.endswith("_bk"):
        pos = np.empty(len(D["order"]), int); pos[D["order"]] = np.arange(len(pos))
        out = []
        for i in idx:
            cand = [i]
            for d in (1, -1, 2, -2, 3, -3):
                cand.append(D["order"][(pos[i] + d) % len(pos)])
            for c in cand:
                if g[c] == 0 or rng.random() >= PLACE_REFUSE:
                    out.append(c); break
        idx = np.array(out)
    else:
        keep = (g[idx] == 0) | (rng.random(len(idx)) >= PLACE_REFUSE)
        idx, wt = idx[keep], wt[keep]
        if len(idx) == 0: idx, wt = None, None
    return idx, (np.ones(len(idx)) if idx is not None else None)

def run(T, reps=300, scen=None):
    D = prepare(T); letters = D["letters"]
    ag = AGREEMENTS.get(T, []); yc = ["y_" + l for l in letters]
    shy = letters[int(np.argmax(D["truth"][:-1]))]
    tv = dict(zip(yc, D["truth"] * 1e6)); tseats = seats_of(tv, yc, ag)
    rows = []
    scen = scen or SCEN
    cells = [(s, M_BASE, n) for s in scen for n in NS] + ([("none", m, n) for m in (50, 200) for n in NS] if "none" in scen else [])
    for sc, m, n in cells:
        Q = lie(D["S"], letters, sc, shy); Qx = lie(D["X"], letters, sc, shy)
        for di, design in enumerate(DESIGNS):
            if m != M_BASE and design != "strat_prior":     # interviews-per-place grid only for the reference design
                continue
            rng = np.random.default_rng([T, SCEN.index(sc), m, n, di])
            err = np.empty((reps, len(letters))); sm = np.empty(reps)
            for r in range(reps):
                idx, wt = pick(D, design, n, rng)
                if sc in ("place_refuse", "hard_both"):
                    idx, wt = _refuse(D, idx, wt, design, sc, rng)
                if idx is None or len(idx) == 0:
                    th = (D["X"] * D["sz"][:, None]).sum(0) / D["sz"].sum()
                else:
                    th = estimate(D, design, idx, wt, m, rng, Q, Qx)
                err[r] = th - D["truth"]
                s = seats_of(dict(zip(yc, th * 1e6)), yc, ag)
                keys = set(s) | set(tseats)
                sm[r] = sum(abs(s.get(k, 0) - tseats.get(k, 0)) for k in keys) / 2
            j = letters.index(shy)
            rows.append(dict(T=T, scenario=sc, design=design, n_places=n, m=m, reps=reps,
                             share_mae_pp=100 * np.abs(err).mean(),
                             share_max_pp=100 * np.abs(err).max(1).mean(),
                             top_list=shy, top_bias_pp=100 * err[:, j].mean(), top_sd_pp=100 * err[:, j].std(),
                             seats_misallocated=sm.mean(), seats_ge3=float((sm >= 3).mean()),
                             places_total=len(D["w"])))
    return pd.DataFrame(rows)

def select_sample(T, n=60, seed=0):
    """Places to interview for election T: systematic PPS along the order of the previous election's profile.
    Needs the list of places of T (public before election day) and the results of T-1. Returns the chosen places."""
    D = prepare(T); idx, _ = pick(D, "strat_prior", n, np.random.default_rng(seed))
    f = D["frame"].iloc[idx]
    out = f[["loc_name", "loc_code", "station", "registered", "valid"]].copy()
    out["prior_rank_in_order"] = [int(np.where(D["order"] == i)[0][0]) for i in idx]
    return out.sort_values("prior_rank_in_order").reset_index(drop=True).drop(columns="valid")

def envelopes():
    """Votes cast in external envelopes (code 9999: soldiers, diplomats, prisoners, hospitals...) are in no box sample.
    How big is the miss, and does adding the PREVIOUS election's envelope profile help? Uses actual K22-25 results."""
    rows = []
    for T in (22, 23, 24, 25):
        D = prepare(T); letters = D["letters"]; ag = AGREEMENTS.get(T, []); yc = ["y_" + l for l in letters]
        cur, prv = load_history(T), load_history(T - 1)
        def votes(df, env):
            d = df[df.is_envelope == env]; pc = [c for c in df.attrs["party_cols"]]
            v = np.array([d[l].sum() if (l != "other" and l in d) else 0.0 for l in letters])
            v[-1] = d.valid.sum() - v[:-1].sum(); return v
        reg, env = votes(cur, False), votes(cur, True)
        penv_prev, preg_prev = votes(prv, True), votes(prv, False)
        e_share = env.sum() / (reg.sum() + env.sum()); e_prev = penv_prev.sum() / (penv_prev.sum() + preg_prev.sum())
        full = (reg + env) / (reg + env).sum(); boxes = reg / reg.sum()
        corr = (1 - e_prev) * boxes + e_prev * penv_prev / penv_prev.sum()
        def seats(sh): return seats_of(dict(zip(yc, sh * 1e6)), yc, ag)
        def mis(a, b):
            ka = set(a) | set(b); return sum(abs(a.get(k, 0) - b.get(k, 0)) for k in ka) / 2
        sf = seats(full)
        rows.append(dict(T=T, envelope_share_pct=100 * e_share, prev_envelope_share_pct=100 * e_prev,
                         boxes_only_mae_pp=100 * np.abs(boxes - full).mean(), boxes_only_max_pp=100 * np.abs(boxes - full).max(),
                         boxes_only_seats_off=mis(seats(boxes), sf),
                         with_prev_envelopes_mae_pp=100 * np.abs(corr - full).mean(),
                         with_prev_envelopes_max_pp=100 * np.abs(corr - full).max(),
                         with_prev_envelopes_seats_off=mis(seats(corr), sf)))
    return pd.DataFrame(rows)

def main():
    from multiprocessing import Pool
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    sub = sys.argv[2].split(",") if len(sys.argv) > 2 else None     # run scenarios in parts: python -m model.exitpoll 300 none,noise10 part1.csv
    if len(sys.argv) > 3:
        with Pool(5) as p:
            pd.concat(p.starmap(run, [(T, reps, sub) for T in (22, 23, 24, 25, 26)])).to_csv(sys.argv[3], index=False)
        return
    with Pool(5) as p:
        dfs = p.starmap(run, [(T, reps, sub) for T in (22, 23, 24, 25, 26)])
    out = pd.concat(dfs); os.makedirs("results", exist_ok=True)
    out.to_csv("results/exitpoll.csv", index=False)
    envelopes().to_csv("results/exitpoll_envelopes.csv", index=False)
    select_sample(26, 60, 26).to_csv("results/exitpoll_example_sample_k26.csv", index=False)
    print(out[(out["T"].isin([22, 23, 24, 25])) & (out.m == M_BASE)].groupby(["scenario", "design", "n_places"])[["share_mae_pp", "seats_misallocated"]].mean().round(2).unstack("n_places").to_string())

if __name__ == "__main__":
    main()
