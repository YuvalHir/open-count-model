# Pre-registration sizemodel-v1 (Claude-ideas 2, size part). Written 29.10.2026 ~23:58 IST, before any run.
Motivation: decomp-v1 (results/decomp.csv) shows that under a RANDOM order about 85% of the share error (0.21 of 0.25 pp) comes from box SIZES; under biased orders the shares dominate.
Data label: DEVELOPMENT, pairs T=22..26 (K26 not a holdout). Simulated arrival orders. Counted fractions 5% and 20%. Orders: random (3 seeds), low_likud_first, small_first, low_turnout_first.
Variants (everything else = frozen project.py, lam=5):
- base: size = prev_valid * global growth ratio (published).
- size_ridge: ridge (lam=5) of log((valid+1)/(prev_valid+1)) on the same T-1 features (xcols incl. turnout, log registered) fitted on COUNTED stations with prev_valid>0, predicts uncounted boxes; clipped to +/-0.7 in log; stations with prev_valid=0 use the global ratio on 1 + average size... (use the counted median valid).
- size_reg: size = registered_T-1 only through ratio of counted (valid/prev_registered), i.e. growth in voters per T-1 registered. 
Metric: share MAE pp and seats misallocated; paired difference vs base per (T, order, seed, frac); 95% bootstrap CI over those units.
Success rule (fixed now): adopt a variant only if it lowers share MAE in the random order AND does not raise it by more than 5% in any biased order, on at least 4 of 5 pairs. Otherwise report as no gain / worse. No tuning after seeing results.
