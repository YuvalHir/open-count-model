# Pre-registration decomp-v1: where does the projection error come from? (Claude-idea 1)
Written 29.10.2026 ~23:57 IST, before any run. Data label: DEVELOPMENT, all pairs K21->K22 ... K25->K26 (T=22..26). K26 is not a holdout. Arrival orders are SIMULATED (past real orders are not public).

Question: of the projection error under a biased order, how much comes from wrong box sizes (valid votes of uncounted boxes) vs wrong shares (list shares in uncounted boxes)?
Variants (same ridge, lam=5, frozen code of model/project.py):
- base: as published.
- oracle_size: true valid votes for each uncounted box, predicted shares.
- oracle_share: predicted sizes, true list shares for uncounted boxes.
- oracle_both: must give zero error (sanity check).
Settings: orders random, low_likud_first, small_first, low_turnout_first; counted fraction 5% and 20%; seeds 0 (random order seeds 0-2). Metrics: mean abs share error (pp), seats misallocated. Report mean over T=22..26 and per T.
Prediction (written before running): sizes explain the minority of the error (oracle_share, i.e. only size error, stays below half of base share error) in the biased orders. If this is false, we say so.
No code or parameter changes follow from this study; it is diagnostic only. Result is reported whatever it is.
