# Pre-registration round3-v1 (Claude round-3 ideas 1, 7, 2, 3). Written 30.10.2026 ~00:55 IST, before any of these runs.
Method-v2 stays frozen; everything here is a challenger. Development T=23..26 (K26 not a holdout); holdout T=20,21 (K19 cannot run transfer-based methods). Reported separately. Orders are simulated.

## Check of Claude's claim about the base ridge (diagnostic, written after reading model/project.py before running)
Code facts (read, not run): ridge_fit_predict uses lambda=5 on standardized features with weights sqrt(valid) (about 20 per place, summed over counted places). With >=120 counted places the data term is ~2400+ versus lambda 5, so base ridge is effectively unpenalised OLS. Claim looks TRUE. In fit_P (transfer) the penalty is kappa*W*||P-P0||^2 with W = sum of counted weights, so it grows with the number of counted places and never washes out. Also TRUE by reading. Test: base ridge with lambda scaled 5, 5e2, 5e3, 5e4 (diagnostic only).

## Idea 1: diagnose the transfer random-order loss
Variants (T>=20): transfer (kappa 0.02, as method-v2 challenger); transfer_const: penalty fixed at kappa*W_ref with W_ref = valid votes of 1% of places, so it washes out as more places are counted; oracle_P: P fitted on ALL places of the current election with no penalty (uses truth, diagnostic floor, not usable live).
Decision rule (Claude's, 1.5x base): oracle_P random-order 20% share MAE >= 1.5x base -> model-class bias (row-stochastic, no intercept). Else if transfer_const random 20% <= 1.5x base while transfer is above -> the penalty scaling is the cause.

## Idea 7: severity-graded orders (the evaluation grid for everything below)
Order key = beta*z_i + Gumbel noise, z = standardised previous-election Likud share of the place, lowest key first. beta in {0, 0.5, 1, 2, 4, 8} (beta=0 is random; 8 is near-deterministic low-Likud-first), 3 seeds each; plus small_first and low_turnout_first. Counted 1/5/20/40%.
Success rule for any candidate method (Claude's, adopted): share MAE never worse than +5% of base at any beta and fraction in {1,5,20,40}% AND >=20% better than base at beta 4 and 8 at 1% and 5% counted. On development AND holdout. Otherwise not adopted.

## Idea 2: offset ridge with transfer prior mean
y_i ~ x_i P0 + A_i b, b ridge, P0 = same prior as transfer (previous pair, past-only). Weights = valid votes (not sqrt); features standardised (the model's x columns). lambda chosen by an earlier-pair-only procedure (assumption: our simplification of Claude's empirical Bayes sigma^2/tau^2): on the previous pair (T-1 vs T-2, its own prior from T-3->T-2), random 50/50 split of places (seed 0), both directions, lambda from {1e2,1e3,1e4,1e5,1e6,1e7} minimising weighted share MSE. One lambda per election pair. If K17 data cannot be loaded for T=20, T=20 is skipped for this method and reported.

## Idea 3: prequential stacking (Dawid)
Models: base, transfer (kappa 0.02), offset (idea 2). Batches of 1% of places in arrival order. Each batch is scored by each model fitted on the places before it (weighted mean squared share error, weights valid votes). Weights equal until 3 batches are scored, then w_m proportional to exp(-eta * cumulative loss_m), eta = 1/(mean over models of the mean batch loss in the first 3 scored batches). Blend = weighted mean of the three models' share predictions for the uncounted places. No tuning.

Results are reported whatever they are. No tuning after seeing results.
