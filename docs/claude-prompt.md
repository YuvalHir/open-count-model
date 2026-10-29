# Prompt to paste into Claude: sharpen an open Knesset-seat prediction model

You are a statistician / election-forecasting researcher. Below is the full state of an open-source project (MIT, https://github.com/YuvalHir/open-count-model). I want concrete, testable ideas to make it more precise, ranked, each with a way to test it. Read all of it, including the negative results, before proposing anything. Do not repeat things already tried unless you can say why the earlier test was inadequate.

## 1. The problem
Israeli elections (Knesset, 120 seats, 3.25% threshold, Bader-Ofer with surplus-vote agreements). On election night the Central Elections Committee (CEC, ועדת הבחירות המרכזית) publishes results polling station by polling station as counting ends. The order stations appear is NOT random: it depends on station size, location, counting speed, and sector. A raw "counted so far" total is therefore biased early on. Separately, "double envelopes" (soldiers, hospitals, prisoners, diplomats; 6.3-9.6% of valid votes in K22-25) are counted last and vote differently from regular boxes.
Goal: from the stations counted so far, predict the final seat distribution, with honest uncertainty. A closed-source site (Votes26) claims to do this. We do not claim parity with it and have no evidence either way.
Second goal (exit polls): design an exit-poll sample (which boxes, how many interviews) and estimator, using only information available at 22:00 on election day, and compare with TV exit polls.

## 2. Data we have
- CEC final per-box results for Knesset 21-25 (https://votes21.bechirot.gov.il ... votes25.bechirot.gov.il), K26 live files (media26.bechirot.gov.il/files/expb.csv, expc.csv; updated a few times per hour, protected by a browser check).
- Per box: locality code, box number (sub-boxes like 5.1, 5.2 are merged to "place 5"), registered voters, voters, valid votes, votes per list. No address or coordinates in these files. Box numbers change between elections (merges, splits, renumbering).
- CEC polling-place address lists for K21-25 and a K26 govmap layer (used for address matching, see below).
- Final per-box turnout exists for K21-25. Intraday per-box turnout (20:00 file) exists for K26 only.
- National turnout by hour for K21-26 (data/turnout_national.csv).
- TV exit polls K21-K26 first-published lists (data/tv_exit_polls/tv_exit_polls.csv, source link per row).
- Real arrival orders of past elections are NOT public. All backtests use simulated orders: random, small places first, large first, low turnout first, low-Likud first, high-Likud first (the last ones are deliberately hard). Real orders are probably between random and biased.
- K26 (29.10.2026): 12,005 regular boxes in the live file (regular box count has been stable for hours), envelopes still arriving.

## 3. The model (frozen at tag matching-rules-v1)
- Unit: voting place = (locality, integer part of box number).
- Features of place in election T: shares of each T-1 list (lists >= 0.5% nationally, rest pooled), T-1 turnout, log registered. Targets: shares of each T list (>= 0.3% nationally, rest pooled).
- One multi-output ridge regression (lambda 5, weights sqrt(valid votes)) fit on places counted so far, predicts uncounted places. Uncounted place size = T-1 valid votes times the counted growth ratio. Total = counted + predicted uncounted, then Bader-Ofer (reproduces official K25 allocation).
- Uncertainty: cluster bootstrap over localities + resampled locality-level residuals scaled by 1/sqrt(size). Nominal 80% interval had actual coverage about 85% at 2-20% counted and 93% at 40% under random order; under biased orders the intervals are too narrow (not measured).
- Matching between elections: only 62-97% of votes can be matched by (locality, place) because numbering changes. Unmatched places get a size-based fill (profile of their locality, else national). Match rate by pair (votes matched): K21->22 99%, 22->23 97%, 23->24 97%, 24->25 92%, 25->26 76% (the weak spot).
- Envelopes: not in the seat projection yet. A separate test predicts envelope list shares from regular-box shares plus the average historical (envelope - regular) gap.

## 4. What we measured (metric: seats out of place = half the sum of absolute seat differences over lists, out of 120)
Backtest, K22-26 replays, random arrival order (development data; K26 included but it is not a holdout):
- Counted 5%: model 2.1 vs raw counted total 5.1. 20%: 1.8 vs 2.6. 40%: 1.3 vs 1.7.
- Worst biased order (low-Likud first), 20% counted: model 21 vs raw 76 seats out of place. At 1% counted under biased order the model is still about 69 out of place. The model removes much of the bias but is far from solved.
Experiments (all in results/experiments.csv; a 5% relative change in error is called better/worse, else no effect; this rule was fixed after the experiments ran):
- Better: projection vs raw (above); size-based fill of unmatched places raised match from 83% to 92% of votes (but see below); size of a box predicted from the 20:00 turnout file instead of last election's size cut share error 18% (K26 development data only); envelope history lean cut envelope share error 6% (0.565 -> 0.531 pp, K25 held out, misses new swings such as Religious Zionism 15.5% true vs 11.2% estimated).
- No effect: size-based fill of unmatched places on projection error (match rate rose, share error changed 3%); address-based place matching (K25 profile error down, no K26 gain); choosing hyperparameters by leave-one-election-out (held-out seats 4.43 vs 4.39 default); turnout share as a model feature.
- Worse: an address-matching variant that reuses addresses (higher match rate, share error +18%).
Lesson: a higher match rate does not automatically improve the seat projection.

## 5. Exit-poll design study (simulation on K22-25 actual box results; development data)
Designs compared: plain draw of boxes proportional to size (pps_ratio); stratified draw by previous-election profile + prior-based correction (strat_prior); plus backup boxes if a box refuses; plus "who did you vote for last time" weighting; plus group-weighted model-assisted (GREG-style) estimator = the "ideal" design (strat_greg_ps_bk); turnout-weighted size variant.
- Without behaviour problems, 120 boxes x 200 interviews: plain 6.9 seats out of place, ideal 3.4.
- Harsh assumption set (10% of the biggest list's voters hide their vote and Haredi/Arab boxes refuse): plain 15.5, ideal 7.9. These behaviour assumptions are OURS, not measured.
- Doubling boxes (60 -> 120) cut error 16%; doubling interviews per box (100 -> 200) only 4%. Budget: more boxes beat more interviews because voters in one box are alike (design effect rises with interviews per box).
- Monte Carlo of lying (tag lies-mc-v1, assumed distribution: each list >= 3% lies with p=0.35, hides U(0, 25%) of its voters, direction single-target / spread / inconsistent between current and past-vote answers): ideal design median 6 seats out of place, 90% range 2-12; plain draw median 9 (4-15); the TV mean (4.2) is exceeded in 71% of draws for the ideal design. A milder prior (p=0.15, up to 10%, post hoc) gives median 4 (1-7), TV mean exceeded in 33%. Past-vote weighting alone is unstable when liars are consistent (90th percentile 29 seats in one regime). Which part of our simulation is Monte Carlo: sampling of boxes and respondents, refusals, and now the lie pattern. Fixed assumptions remain: non-response factors (Haredi x0.5, Arab x0.6), the single set of priors above.

## 6. TV exit polls vs final results (pre-registered metric, K21-25, development)
13 broadcaster-election cells scored (Kan 11, Channel 12, Channel 13; K21 from a Wikipedia table, others from first news reports). Mean seats out of place 4.8, range 2-8; K22-25 mean 4.2. Signed group errors (predicted minus final seats, averaged across channels): Arab lists -1.2 in all five elections (TV under-predicts them every time); Likud and Haredi parties no consistent bias; the big misses (K21, K25) come from lists near the threshold (New Right, Zehut, Meretz). K26 provisional (compared with our own live count, NOT official; unofficial): Kan 5, C12 6, C13 5, i24 6, C16 6, C14 10. We do not claim to beat TV.

## 7. Constraints
- Fully open source, MIT. No copying third-party code or data of unclear license. Official CEC data and our own computations only.
- Honesty: label "official (CEC)" vs "our calculation" vs "assumption"; development vs held-out data; keep negative results visible. Never present model output as an official result. No claim of parity with Votes26 and no claim of beating TV polls without real evidence. K26 is not an independent holdout (the model and rules were frozen at tags matching-rules-v1, exitpoll-designs-v1, diagnosis-v1, dashboard-ideal-v1 before K26 results were final; K22-25 are development data).
- Exit-poll estimator may use only information available at 22:00: past results, national turnout so far, the sample itself. No peeking at the CEC count.
- Pre-register metric and design before computing.

## 8. Open questions (where we want your help)
1. Early-count bias under a biased arrival order is the biggest unsolved error (21 seats out of place at 20% counted in the worst case, 69 at 1%). What model structure would be robust to arrival order (hierarchical / multilevel by locality and sector, partial pooling, sector random effects, using arrival-order itself as a covariate, reweighting by station-level "lateness")? How to test without real orders (we only started recording real K26 arrival order after most regular boxes were already in the file)?
2. Place matching K25 -> K26 is only 76% of votes. Ideas to raise it that actually improve the projection (cumulative-size alignment within locality, registered-voters ratio, many-to-one and one-to-many splits, address + coordinates with a trust rule, locality or neighbourhood profile instead of a global one for unmatched places). How to measure improvement of the projection, not only match rate?
3. Envelopes: a proper model for double-envelope votes (6-10% of votes; leans differ by election), with uncertainty, wired into seats.
4. Small lists near 3.25%: P(crossing threshold) and seat flips. Our biggest misses are there.
5. Interval calibration under biased orders and for seat counts (not just shares).
6. Exit-poll: better estimators under unknown lying and non-response; using only 22:00 information; how to combine an exit sample with the live CEC count after polls close (needs its own pre-registration and legitimacy discussion).
7. Anything we mis-specified (loss function, ridge vs hierarchical Bayes, transfer-matrix models, ecological-inference concerns, cluster bootstrap validity).

## 9. Output wanted
A ranked list (max 10) of concrete, testable ideas. For each: the idea in 2-3 sentences; why it should help (mechanism); exactly how to test it on our data with development vs held-out discipline (what to pre-register, metric, baseline, expected effect size, what result would count as failure); risk of overfitting or dishonest claims; implementation cost (hours). Put quick wins first. Call out any idea that sounds good but our evidence already contradicts. Finish with the three experiments you would run first this week.
