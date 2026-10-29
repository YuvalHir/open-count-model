"""Model forecast for the CURRENT 2026 count: regular boxes in the file + projected remaining envelopes.

Key fact (measured, see docs): the latest CEC file already holds ~11,970 regular boxes (K25 had 11,707), so the regular
count looks essentially complete; what is still arriving is mainly the external envelopes (loc_code 9999).
ASSUMPTION (not verified): regular boxes in the file are complete. Output is model output, not an official result.

    python -m model.live_forecast       -> prints table, writes results/live_forecast.json
"""
import json, os, warnings
warnings.filterwarnings("ignore")
import numpy as np
from .load import load_history, load_live, live_snapshots
from .backtest import AGREEMENTS
from .seats import allocate

def env_stats():
    """Historical envelope/regular valid ratio and mean (envelope share - regular share) per list letter, K22-25."""
    ratios, lean = {}, {}
    for T in (22, 23, 24, 25):
        d = load_history(T); pc = d.attrs["party_cols"]
        e, r = d[d.is_envelope], d[~d.is_envelope]
        ratios[T] = float(e.valid.sum() / r.valid.sum())
        for c in pc:
            lean.setdefault(c, []).append(float(e[c].sum() / e.valid.sum() - r[c].sum() / r.valid.sum()))
    return ratios, {c: float(np.mean(v)) for c, v in lean.items() if len(v) >= 3}

def run(n_draws=2000, seed=0):
    stamp, path = live_snapshots()[-1]
    d = load_live(path); pc = d.attrs["party_cols"]
    reg, env = d[~d.is_envelope], d[d.is_envelope]
    R = reg[pc].sum().values.astype(float); E = env[pc].sum().values.astype(float)
    Rv, Ev = float(reg.valid.sum()), float(env.valid.sum())
    ratios, lean = env_stats()
    rlo, rhi = min(ratios.values()), max(ratios.values())
    p_env_seen = E / E.sum()
    base = R / R.sum() + np.array([lean.get(c, 0.0) for c in pc])      # new lists: lean 0
    base = np.clip(base, 0, None); base /= base.sum()
    rng = np.random.default_rng(seed); ag = AGREEMENTS[26]
    tot = np.zeros((n_draws, len(pc))); seats = []
    for i in range(n_draws):
        r = rng.uniform(rlo, rhi)
        rem = max(r * Rv - Ev, 0.0)
        w = rng.uniform()
        p = w * p_env_seen + (1 - w) * base
        v = R + E + rng.multinomial(int(rem), p / p.sum())
        tot[i] = v
        seats.append(allocate(dict(zip(pc, v)), ag, 0.0325))
    lists = [c for c in pc if any(s.get(c, 0) for s in seats)]
    out = dict(snapshot=stamp, assumption="regular boxes in the file are complete (not verified)",
               regular_valid=Rv, envelope_valid_so_far=Ev, env_ratio_hist=ratios,
               env_remaining_votes_range=[max(rlo * Rv - Ev, 0), max(rhi * Rv - Ev, 0)], lists={})
    for c in lists:
        a = np.array([s.get(c, 0) for s in seats]); i = pc.index(c)
        out["lists"][c] = dict(votes_counted=float(R[i] + E[i]), share_counted_pct=100 * float((R[i] + E[i]) / (Rv + Ev)),
                               seats_median=float(np.median(a)), seats_lo=float(np.quantile(a, .1)), seats_hi=float(np.quantile(a, .9)),
                               p_in_knesset=float((a > 0).mean()))
    return out

if __name__ == "__main__":
    o = run()
    os.makedirs("results", exist_ok=True)
    json.dump(o, open("results/live_forecast.json", "w"), ensure_ascii=False, indent=1)
    print(o["snapshot"], "regular valid %d, envelopes so far %d, remaining envelope votes range %s" % (o["regular_valid"], o["envelope_valid_so_far"], [int(x) for x in o["env_remaining_votes_range"]]))
    for c, v in sorted(o["lists"].items(), key=lambda kv: -kv[1]["seats_median"]):
        print(f"{c:5s} counted {v['share_counted_pct']:5.2f}%  seats {v['seats_median']:.0f}  80% [{v['seats_lo']:.0f},{v['seats_hi']:.0f}]  P(in) {v['p_in_knesset']:.2f}")
