# Prompt v3 for Claude: keep the early-count gain without the late and random-order cost

You are a statistician / election-forecasting researcher. This is round 3 on an open-source project (MIT, https://github.com/YuvalHir/open-count-model). In rounds 1 and 2 you gave ideas; we pre-registered and ran them. Read sections 3-6 before answering: they say what is settled. I want ONE focused thing (section 7) plus a few genuinely different ideas. Do not repeat anything in section 6.

## 1. The problem
Israeli elections (Knesset, 120 seats, 3.25% threshold, Bader-Ofer with surplus-vote agreements). On election night the Central Elections Committee (CEC) publishes results polling station by polling station as counting ends. The order is NOT random (station size, location, counting speed, sector), so the raw "counted so far" total is biased early. Double envelopes (soldiers, hospitals etc., 6.3-9.6% of valid votes) are counted last. Goal: predict final seats from the stations counted so far, with honest uncertainty. A closed-source site (Votes26) claims to do this; we claim no parity with it and have no evidence either way. Second goal: exit-poll design (not the focus this round).

## 2. Data and honesty labels
- Official CEC per-box files K16-25 (data.gov.il), K26 live files recorded by us. K26 count complete: our calculation from the last CEC live file (12,018 regular boxes, 908 envelope rows, 5,690,682 valid) equals the announced seats (Likud 27, Yashar 21, Beyachad 12, Joint List 11, Democrats 8, Ra'am 8, YB 7, Otzma 7, UTJ 7, Shas 6, RZ 6). Formal CEC publication due 4.11.2026; we treat it as final with a footnote.
- Arrival order of past elections is NOT public: every backtest uses SIMULATED orders (random x3 seeds, small first, low turnout first, low-Likud first), counted 1/5/20/40%.
- DEVELOPMENT data: K22-26 (K26 is not a holdout). TRUE HOLDOUT: K19-21 (official CEC per-box files, never scored before tag holdout-v1; K19-21 seat numbers are our calculation without agreements). Method frozen at tag method-v2 (30.10 00:13). Challenger tags: decomp-v1, sizemodel-v1, swing-v1, matchsens-v1, ideas569-v1, round2-v1, holdout-v1, data-plan-v1, cbs-v1, switch-v1.

## 3. The model (frozen at tag method-v2)
- Unit: voting place = (locality, integer part of box number). Features in election T: shares of each T-1 list (>=0.5% nationally, rest pooled), T-1 turnout, log registered. Targets: T list shares (>=0.3%, rest pooled).
- One multi-output ridge (lambda 5, weights sqrt(valid)) fit on places counted so far predicts uncounted places. Uncounted place size = T-1 valid votes x counted growth ratio. Total = counted + predicted, then Bader-Ofer with agreements.
- Uncertainty: cluster bootstrap over localities + resampled locality residuals.
- Matching between elections: votes matched by (locality, place): K21->22 99%, 22->23 97%, 23->24 97%, 24->25 92%, 25->26 76%. Unmatched places get their locality profile (else national).
- Envelopes (6.3-9.6% of valid votes): not in the seat projection. Separate estimator: regular-box shares + mean historical gap.

## 4. Results so far (share MAE in pp; seats out of place = half the sum of absolute seat differences, out of 120)
Round 1 (see v2 prompt, summarised): error under biased orders is in SHARES, under random order in SIZES. Size model, national swing target, past-vote raking: REJECTED. Envelope ratio model: not adopted. Seat intervals under-cover under biased orders (80% interval covers 36-80% of lists at 5% counted). 76% match rate costs almost nothing.

Round 2 (round2-v1, development T=23..26; transfer needs the previous pair):
- Idea 1 diagnostic: base share MAE rank-correlates 0.83 with the OBSERVABLE gap g (L1 distance, in pp, between previous-election shares of counted places and of all places, computable live) and 0.85 with the hidden swing gap h. Cannot be told apart.
- Idea 2 covariate-shift importance weights: REJECTED (low-Likud-first 5%: 7.18 -> 7.66; small-first 5%: 0.89 -> 1.40; random unchanged).
- Idea 3 prior-centred transfer model (row-stochastic matrix P of previous lists to current lists, estimated on counted places, penalty kappa towards P0 from the previous pair; kappa 0.02): REJECTED by the rule, but it is the strong lead. Share MAE, base vs transfer:

| order | counted | base | transfer |
|---|---|---|---|
| low-Likud-first | 1% | 7.80 | 2.87 |
| low-Likud-first | 5% | 7.18 | 2.94 |
| low-Likud-first | 20% | 2.34 | 1.93 |
| low-Likud-first | 40% | 0.62 | 0.85 |
| low-turnout-first | 1% / 5% / 20% | 4.09 / 1.13 / 0.42 | 1.56 / 1.33 / 1.11 |
| small-first | 1% / 5% / 20% | 2.43 / 0.89 / 0.51 | 1.23 / 1.13 / 1.07 |
| random | 1% / 5% / 20% / 40% | 0.48 / 0.25 / 0.18 / 0.13 | 0.96 / 0.90 / 0.75 / 0.56 |
Seats out of place at 5% counted: low-Likud-first 58 -> 28, random 2.3 -> 9.2. kappa 0.2 is worse everywhere than 0.02. So: transfer is far better early under politically biased orders and much worse under random order and late.
- Idea 4 (state-dependent interval width) logged, not run.

Holdout K19-21 (holdout-v1, TRUE holdout): the bias-correction advantage of the model over the raw total is confirmed (low-Likud-first, 20% counted, seats out of place model vs raw: 19 vs 71, 13 vs 75, 31 vs 77). The random-order advantage is NOT confirmed: K21 share MAE 0.37 vs raw 0.18; K19 random 20% seats model 2.0 vs raw 0.67. The transfer model reproduces both its early lead and its random-order loss on K20-21.

CBS socio-economic index per locality (cbs-v1; CBS license allows use with attribution; coverage 99.5% of votes K22/K25): two extra ridge features. NO GAIN (rule: -10% in biased and <= +5% random). Low-Likud-first 20%: 2.34 -> 2.22; random 20%: 0.179 -> 0.184; holdout +0 to +4%. Caveat: the 2021 index is later than K19-24.

Switch by visible shift g (switch-v1): use transfer when g exceeds the 95th percentile of g for the same number of randomly drawn places (computed from previous-election data only, no tuning), else base. Seats out of place at 5% counted, base -> switch: low-Likud-first K23-26 61.5 -> 27.8, holdout K20-21 62.5 -> 36.0. Random: dev 2.3 -> 3.4 (switches 8% of the time at 5%, 33% at 20%), holdout unchanged. Late counts (20-40%) and small-first/low-turnout at 20%+: switching HURTS (base better). NOT ADOPTED: fails on development random order (+29% share MAE at 5%).

Overall honest picture: strong gain over the raw total under biased orders (both development and holdout); no gain beyond the current method in random order; the one open finding is the early transfer gain under biased orders and its late/random cost. All order simulations are ours; real orders may differ.

## 5. Round-1 and round-2 ideas (do not repeat)
R1: error decomposition; size model; compositional swing with shrinkage; locality random effects; seat-level draws and Brier; envelope ratio; arrival-order model (needs real past orders: unavailable); match-rate sensitivity; exit-poll past-vote raking; log score/Aitchison and a frozen tag.
R2: selection-mechanism diagnostic (g, h); importance weights; prior-centred transfer model; state-dependent interval width (logged only); threshold-list beta-binomial; sector slopes; exit-poll sensitivity intervals; social-circle question (field pilot, not run).
## 6. Already tried: do not repeat
All of section 4 plus: size-based fill of unmatched places, address matching/reuse, box splitting, cumulative-voter alignment (match 76 -> 89% but error +25% worse), leave-one-election-out hyperparameters, turnout as feature, box size from the 20:00 turnout file (K26 only), CBS index as ridge feature, the g-threshold switch with the 95th-percentile null, kappa 0.2, past-vote rake, importance weights, envelope ratio. TV exit polls K21-25: mean 4.8 seats out of place; K26 vs our count: Kan 5, Ch12 6, Ch13 5, i24 6, Ch16 6, Ch14 10.

## 7. The one focused ask
Early under biased orders the transfer model cuts error by 40-65% and the observable gap g tells us we are in that regime; later, and under random order, it costs 2-5x. A hard switch with a theory threshold failed because the switch statistic is noisy and the cost of a false switch is large. We want a way to KEEP the early gain without the late/random cost, with no tuning on K22-26. Directions we want your view on (rank and refine; do not just list):
- Principled blending: weights from a model (e.g. Bayesian model averaging, stacking by observed g and counted fraction, or a shrinkage of the transfer matrix towards identity-like P0 whose strength follows the number and spread of counted places), not a threshold.
- Uncertainty-aware shrinkage: kappa as a function of the effective number of independent counted places and of g, derived from theory (a hierarchical or empirical-Bayes prior), checked on K23-26 and K20-21.
- Sequential / online approaches: update P as places arrive, test whether the order itself is informative (a hidden-state model of counting speed by sector), change-point detection for "this order is biased".
- Seat uncertainty: intervals that widen with g (the logged idea 4, but with a better construction).
- Anything genuinely different (ecological inference, hierarchical sector model without place matching, using the arrival order of places as a feature, different loss).
Do not propose things that need real past arrival orders (we have none), or non-open data.

## 8. Constraints
- Fully open source, MIT. No copying third-party code or data of unclear license. Official CEC data and our own computations only.
- Honesty: label "official (CEC)" vs "our calculation" vs "assumption"; development vs held-out data; keep negative results visible. Never present model output as an official result. No claim of parity with Votes26 and no claim of beating TV polls without real evidence. K26 is not an independent holdout (the model and rules were frozen at tags matching-rules-v1, exitpoll-designs-v1, diagnosis-v1, dashboard-ideal-v1 before K26 results were final; K22-26 are development data).
- Exit-poll estimator may use only information available at 22:00: past results, national turnout so far, the sample itself. No peeking at the CEC count.
- Pre-register metric and design before computing.

## 9. Output wanted
A ranked list (max 8) of concrete, testable ideas NOT in sections 5 and 6. For each: 2-3 sentence idea; mechanism; exact test with development (K23-26) vs holdout (K20-21; K19 for non-transfer methods) discipline; what to pre-register; metric and baseline; expected size of effect; the success rule AND the failure rule, written so a negative result is unambiguous; overfitting/honesty risks; cost in hours. Say which ideas our evidence already contradicts. Finish with the three experiments to run first, in order, each with a pre-registered threshold that is fixed from theory and not tuned on our results. Success rule we will use by default for a blend: at least 20% lower share error than base at 1% and 5% counted in low-Likud-first, AND no more than +5% worse than base at 20% and 40% counted and in random order, on development AND holdout.
