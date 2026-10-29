# Pre-registration round4-v1 (Claude round-3 ideas 4, 5, 6 + bias-meter diagnostic). Written 30.10.2026 ~01:08 IST, before any of these runs.
Method-v2 frozen; all challengers. Development T=23..26, holdout T=20,21, reported separately, same simulated order grid as round3-v1 (Plackett-Luce beta 0,0.5,1,2,4,8 x 3 seeds, small_first, low_turnout_first; counted 1/5/20/40%). Base and transfer_const numbers come from round3-v1 (same orders and seeds). K19 and K22 are not run for transfer-based methods (K22's prior would use K20-21, which were reserved as holdout; K19 has no previous pair in our history). These are our simplified versions of Claude's ideas (assumptions, fixed now).

## Idea 4: support-aware blocked-CV blend of base and transfer_const
Counted places sorted by PC1 of the standardised T-1 feature columns (all places, PCA fitted on all places: uses only T-1 data), split into 5 contiguous blocks. For each held-out block, fit base and transfer_const on the other counted places, score weighted (valid votes) squared share error on the held-out block. Loss L_m = mean over blocks. Weights proportional to exp(-eta L_m), eta = 1/mean(L_base, L_transfer). Blend shares for uncounted places = weighted mean. No tuning.

## Idea 6: Gaussian-process residual on the transfer_const prior mean
Mean = transfer_const prediction. Residuals on counted places R = Y - X P. Kernel ridge (= GP posterior mean) with RBF kernel on the standardised model features, lengthscale = median pairwise distance among counted places (subsample 400), noise-to-signal ratio 0.5 divided by weight (valid votes / mean weight). Prediction = X_u P + K_uc (K_cc + 0.5 diag(1/w))^-1 R, clipped at 0 and renormalised. Fixed now: ratio 0.5, median heuristic.

Success rule for ideas 4 and 6 (round3-v1 rule, unchanged): share MAE never worse than +5% of base at any order and counted fraction in the grid AND >=20% better than base at beta 4 and 8 at 1% and 5% counted. On development AND holdout. Else not adopted.

## Idea 5: intervals scaled by prequential error (national share of each list)
Base model. Batches of 1% of places in arrival order; e_j = aggregate predicted share minus realised share of batch j (weighted by valid votes) for list k, predicted by base fitted on the earlier places. At J% counted: s_k = u * sqrt(mean_j e_jk^2) with u = uncounted vote fraction; 80% interval = point +- 1.2816 s_k. Compared with the existing cluster-bootstrap interval (project_draws, 30 draws, 10th-90th percentile). Orders beta 0, 4, 8 (3 seeds), counted 5% and 20%. Coverage = fraction of lists whose final share lies inside.
Success rule: coverage within [0.70, 0.90] at every beta x fraction cell, on development AND holdout, AND mean width <= 2x the bootstrap width. Else not adopted. Descriptive only (no rule): coverage at 1% and 40%.
Note: this is share coverage, not seat coverage (assumption: seat intervals need the seat draws; not done now).

## Bias meter (diagnostic, no change to forecast)
g (observable gap, as switch-v1) and its random-draw 95th percentile (200 draws, seed 12345, same n) for every grid cell. Report share of cells flagged (g above threshold) per beta and fraction (false alarm rate at beta 0; detection rate at beta >=2), and Spearman of g with base share MAE over all cells, development and holdout.

Results reported whatever they are. No tuning after seeing results.
