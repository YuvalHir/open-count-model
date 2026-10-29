# Pre-registration round2-v1 (Claude round-2 ideas 1, 2, 3; idea 4 logged only). Written 30.10.2026 ~00:14 IST, before any of these runs.
Tag method-v2 (created 00:13) freezes the whole current method: model/project.py, matching rules, exit-poll designs, envelope v1. Anything new below is a challenger, not a change to method-v2.
All DEVELOPMENT data: K22-26 (idea 3: T=23..26 only, because it needs the previous pair for its prior). K26 is not a holdout. Orders are simulated. Counted 1%, 5%, 20%, 40%; orders random (3 seeds), low_likud_first, small_first, low_turnout_first.

## Idea 1: selection-mechanism diagnostic (model/selection.py), no model change
For each (T, order, frac, seed): observable gap g = sum over lists of |T-1 share among counted places - T-1 share among all places| (in pp); hidden swing gap h = sum over lists of |(T share - T-1 share) among counted - same among uncounted| (pp, uses truth, diagnostic only). Report mean g, h and base-model share MAE per cell, and the rank correlation of MAE with g and with h across all cells. Prediction (written now): MAE correlates more with h than with g (the error is mostly conditional change, not visible covariate shift).

## Idea 2: covariate-shift importance weights (model/iw.py)
Logistic regression (ridge 1.0, features = the model's x columns, standardized) of uncounted vs counted places, fitted on all places; r = (q/(1-q)) * (n_counted/n_uncounted); relative ratio w = r/(0.5 r + 0.5); clipped to [0.1, 10]; normalised to mean 1 over counted; multiplied into the ridge weights (sqrt(valid) * w). alpha=0.5 and the clip are fixed now.
Success rule (Claude's, adopted verbatim): at least 15% lower share MAE in biased orders at 5% and 20% counted AND at most +5% in random order.

## Idea 3: prior-centered transfer model (model/transfer.py)
shares of uncounted place i = x_i P, where x_i = T-1 list shares (incl. other), P is a row-stochastic matrix (x lists by y lists) estimated on counted places by weighted least squares (weights valid) plus penalty kappa * W * ||P - P0||^2 (W = sum of counted weights), by projected gradient with row-simplex projection (300 iterations). P0 = same estimator fitted on ALL places of the previous pair (T-2 -> T-1; only past data), lists mapped by letter, new lists get 0 prior, rows renormalised. Place size as in the base model. kappa in {0.02, 0.2} both reported, none chosen after seeing results. T=23..26.
Success rule (Claude's): at least 20% lower share MAE at 1% and 5% counted in biased orders AND within +5% at 20% and 40%, for the same kappa. Else REJECTED.

## Idea 4: logged, not run now
Observable shift severity s (= g above) with state-dependent interval width m(s)=1+c*s, c fit on K22-24, tested on K25 (K26 as second test). Planned for the next round; no result yet.

Results are reported whatever they are. No tuning after seeing results.
