# Pre-registration: Monte Carlo of respondent lying (lies-mc-v1)
Written 29.10.2026 before any result of this study was computed.

## Why
Earlier dashboard grid (dashboard-ideal-v1) used FIXED lying patterns: the biggest list loses 5/10/20% of its voters to the other lists in proportion to their size, or a fixed share answers at random; non-response factors were fixed (Haredi x0.5, Arab x0.6). Only the sampling (which boxes, which people, which box refuses) was Monte Carlo (60 repetitions per cell). Nobody knows how or in which direction people lie, so a fixed scenario overstates what we know.

## Design (everything below is an ASSUMPTION, not a measurement)
Per Monte Carlo draw, a fresh lying pattern is drawn, then one exit-poll sample is simulated and estimated:
- Who lies: each list with at least 3% of the national vote lies independently with probability 0.35 (zero lying lists is possible).
- How many: each lying list hides a share h ~ Uniform(0, 0.25) of its own voters (same h in every box).
- Direction (where the hidden voters say they voted):
  - R1 "coordinated": all liars of a list name the same single other list (drawn uniformly among the other lists with at least 3%), and lie the same way when asked about the previous election (consistent).
  - R2 "spread": liars of a list spread over the other lists with a Dirichlet(1) draw (national, same in every box), consistent on the previous-vote question.
  - R3 "inconsistent": as R2, but the previous-vote answer is truthful (so the weighting by past vote can detect them).
- Non-response is switched off in this study to isolate lying.
- Designs: plain draw by size (pps_ratio), stratified + prior correction (strat_prior), the ideal model (strat_greg_ps_bk, dashboard-ideal-v1), and the past-vote weighting design (strat_prior_pastvote). Sizes: 60 boxes x 100 interviews and 120 x 200.
- Data: K22-K25 (development data). K26 excluded (not final).
- Draws: 300 per (election, design, size, regime). Fixed seeds.

## Outputs (pre-committed)
Per design, size and regime, pooled over K22-25: median, 5th and 95th percentile and mean of seats out of place (half the sum of absolute seat differences over lists). Also the share of draws with error above the TV mean (4.2 seats, K22-25). Compared with the fixed-scenario numbers from the dashboard.
No tuning on these results. Negative results (the ideal model is no better than the plain draw, or the range is huge) are reported as they come.
Label: "our calculation, simulation, assumed lying distribution". Not an official result.
