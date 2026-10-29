# TV exit polls vs official results (first test)
Preregistered in docs/prereg/tv_exit_poll_comparison.md (commit a80b1a7) before any number was computed.
- Predictions: data/tv_exit_polls/tv_exit_polls.csv (every row has a source URL and a note). Tiers: A = election-night news report with full list; B = Wikipedia table row, top-two seats checked against Ynet first-broadcast report (K21); P = partial list, not scored; S = later update, sensitivity only (not in headline numbers).
- Official finals: data/tv_exit_polls/official_final_seats.csv (CEC votes21..25.bechirot.gov.il, all sum to 120).
- Code: model/tv_compare.py, scripts/build_tv_data.py. Output: results/tv_exit_poll_comparison.csv.
- Result (13 channel-election cells): mean seats out of place 4.8, range 2-8 (K22-25 only: 4.2). Our simulation (strat_prior, 60 boxes x 100 interviews, K22-25): 5.1 ideal, 8.8 hard-to-sample assumptions. Simulation is development data and assumptions; NOT evidence of beating TV.
- Limits: small n, integer rounding, TV first values are not always verifiable as the very first broadcast (K24 from Globes 22:48; K21 from Wikipedia), K25 Kan 11 and Channel 13 full first lists not found (excluded), unknown real TV sample sizes. K26 recorded, not scored until official final seats exist.

## Follow-up (diagnosis, budget, dashboard)
- Pre-registrations: docs/prereg/tv_miss_diagnosis.md (tag diagnosis-v1), docs/prereg/dashboard_ideal_model.md (tag dashboard-ideal-v1).
- Code: model/tv_diag.py (TV signed group errors), model/exitpoll_groups.py (simulated group bias), model/exitpoll_budget.py (boxes vs interviews, design effect), model/exitpoll_dash.py (dashboard grid), model/tv_k26_provisional.py (K26 vs OUR provisional count, not official).
- Data: data/tv_exit_polls (now incl. i24NEWS, Channel 16, Channel 14 for K26), data/turnout_national.csv (national 20:00 and final turnout, with sources).
- Results: results/tv_group_errors.csv, exitpoll_group_bias.csv, mechanism_fit.csv, exitpoll_budget.csv, exitpoll_dash.csv, tv_k26_provisional.csv.
- Fixed bug before publication: first dashboard grid had wrong bloc-error columns (letter prefix); regenerated.
