# Pre-registration: interactive dashboard grid and "ideal model" (dashboard-ideal-v1)
Written before running the grid. Code: model/exitpoll_dash.py. Everything is simulation of past elections' real box results under ASSUMED respondent behaviour; nothing is measured behaviour.
## Grid (fixed now)
- Elections: K22-K25 (development data; previous election needed for the box profile, so K21 cannot be simulated), K26 provisional (live count, no envelopes, not a holdout, marked provisional).
- Boxes n in {30,60,120,240}; interviews per box m in {50,100,200,400}.
- Designs: pps_ratio (plain size-weighted draw), strat_prior (stratified by prior profile + prior-corrected estimate), strat_prior_bk (same + backup neighbour boxes when a box refuses), strat_prior_pastvote (adds the "how did you vote last time" question and re-scales respondents so the sample matches the known last result; the only way respondent answers are down-weighted), strat_greg_ps_bk (model-assisted, post-stratified, backups).
- Lying pattern x level: none; shy-top (voters of the largest list name another list) at 5/10/20%; random answers at 5/10/20%.
- Non-response: none; Haredi-list voters answer half as often and Arab-list voters 40% less (assumption); the same plus 50% of Haredi/Arab-profile boxes turning interviewers away.
- Metrics per cell (mean over 60 repetitions): mean share error (pp), seats out of place (primary, same as the TV comparison), absolute error in right-bloc seats (right bloc as in model/bloc_backtest.py, K26: Likud, Shas, UTJ, Religious Zionism, Otzma), absolute error in Arab-list seats.
- Comparison: TV polls' actual seats out of place (results/tv_exit_poll_comparison.csv), K21-K25.
## Ideal model (defined now): stratified PPS sample by prior-election profile, backup boxes, last-vote recall question, model-assisted post-stratified estimator (strat_greg_ps_bk), n=120 boxes x m=200. Reported under every assumption cell, including its failure cases. Real-time combination with the live CEC count is a separate later pre-registration.
## Rules
No cell is tuned to match TV. Results are descriptive. No claim of beating TV from simulation alone.
