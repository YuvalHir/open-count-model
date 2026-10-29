# Pre-registration ideas569-v1 (Claude-ideas 5, 6, 9). Written 30.10.2026 ~00:05 IST, before any of these runs.
All DEVELOPMENT data (K22-K26). K26 is not a holdout; K26 truth is now our calculation from the complete CEC file. Arrival orders are SIMULATED.

## Idea 6: envelope model (model/envelope_models.py)
Predict list shares of the external-envelope votes of election T from regular-box shares of T plus history.
Variants: naive (regular shares); additive (published v1: regular + mean historical gap); ratio (regular * mean historical env/regular ratio per list, renormalised; lists without history: ratio 1).
Two schemes: past-only (history = elections before T, T=23..26) and leave-one-election-out (history = all other of K22-26, T=22..26).
Metrics: mean abs error over lists (share points); seats misallocated when the estimated envelope shares are added to the true regular votes using the TRUE envelope total (isolates the share model).
Rule: ratio replaces additive only if it has lower MAE in at least 3 of the 4 past-only pairs and a lower mean; otherwise "no gain".

## Idea 5: seat-level joint draws (model/seat_draws.py)
Use project_draws (frozen) with 60 draws, run every draw through Bader-Ofer with the agreements, take the seat vector of each draw.
Settings: T=22..26, orders random / low_likud_first / small_first, counted 5% and 20% (random order seeds 0). Metrics (per list, then averaged): (a) Brier score of P(list passes the threshold); (b) coverage of the 80% interval [q10,q90] of seats per list (target 0.80); (c) mean width.
Variant B: widen draws around their median by one national factor s in {1, 1.5, 2, 3, 4}; s for election T chosen from the other four elections as the value whose coverage is closest to 0.80 (leave-one-election-out, same order and counted fraction). Report coverage and Brier with s=1 and with chosen s.
Rule: report as is; calibration is "good" only if coverage is within 0.70-0.90 in random and biased orders on at least 4 of 5 elections.

## Idea 9: raking exit poll to past-vote totals (model/rake_exit.py)
Existing design strat_prior_pastvote already rescales the sample by ONE margin (past vote) and was worse (+65%, run under exitpoll-designs-v1). New variant rake_pg: the same rescaling done separately inside each of the 3 place-profile groups (group sizes and past-vote totals known). Simulation as in model.exitpoll (reps 100, strat designs, places n=60 with m=100 and n=120 with m=200), scenarios none, shy15, hard_nr, noise10_shy15, T=22..26. Compare strat_prior, strat_prior_pastvote, rake_pg: mean seats out of place and share MAE.
Rule: rake_pg counts as better only if it beats strat_prior by >=5% in the mean of scenarios with non-response (shy15, hard_nr) AND not worse by >5% in scenario none. Note: a full joint (current x past vote) rake needs the joint table, which we do not have; this is the version the data allow, an assumption.
