# Pre-registration swing-v1 (Claude-idea 3). Written 29.10.2026 ~23:58 IST, before any run.
Data label: DEVELOPMENT, pairs T=22..26, simulated orders (random x3 seeds, low_likud_first, small_first, low_turnout_first), counted 1%, 5%, 20%, 40%. K26 not a holdout.
Variants (sizes = base global ratio in all):
- base: published ridge.
- swing_full: share of list p in uncounted box i = x_ip * exp(b_p) / sum_q x_iq exp(b_q), where x = T-1 share of the matched box (or fallback profile) and b_p = log( counted-boxes current share of p / counted-boxes T-1 share of p ) (national log swing from counted boxes, valid-weighted), floored at share 0.002 before logs.
- swing_half: same with b_p multiplied by 0.5 (the shrinkage is fixed now, not tuned).
Metric: share MAE pp, seats misallocated; paired differences vs base, 95% bootstrap CI over (T, order, seed, frac) units.
Adoption rule: lower share MAE in random AND no more than 5% higher in any biased order, on >=4 of 5 pairs. Otherwise report as no gain or worse. No tuning afterwards.
