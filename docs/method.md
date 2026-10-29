# Method (v1)

Unit: a voting place = (locality code, integer part of the CEC box number). Box numbers like
5.1, 5.2, 5.3 are sub-boxes of place 5 and are merged. Box numbering changes between elections, so
only 62-97% of votes (by election) can be matched to the previous election by (locality, place);
the rest use the previous-election profile of their locality (or the national profile).
Better matching needs addresses/coordinates (not in the CEC files; to do).

Features for each place in election T: shares of each T-1 list (lists >= 0.5% nationally, rest pooled),
T-1 turnout, log registered voters. Targets: shares of each T list (>= 0.3% nationally, rest pooled).
Model: one multi-output ridge regression (lambda 5, weights sqrt(valid votes)), fit on places counted
so far, predicting uncounted places. It learns vote transfers between old and new lists
(e.g. "Yesh Atid voters of 2022 now vote Yashar") without a hand-made party mapping.
Uncounted place size = its T-1 valid votes times the counted growth ratio.
Total = counted votes + predicted uncounted votes, then Bader-Ofer with surplus agreements
(`model/seats.py`; reproduces the official Knesset 25 allocation, `tests/test_seats.py`).

Uncertainty (`project_draws`): cluster bootstrap over localities (parameter uncertainty) plus resampled
locality-level residuals scaled by 1/sqrt(size). Heuristic; checked by `model/coverage.py`.

Not modelled yet: external envelopes ("double envelopes", loc_code 9999). In Knesset 22-25 they were
6.3-9.6% of valid votes and leaned differently from regular boxes (see `out/envelopes.txt`, e.g. Hadash-Ta'al
4.3% vs 11.0% in K22; Religious Zionism 15.5% vs 10.3% in K25). In 2026 the file shows 378 envelope boxes (195,489 valid votes)
at the first snapshot, so the final batch is still to come. Needs its own component.

Also not modelled: sector random effects, correlation of errors across lists beyond the bootstrap,
late changes to station numbering inside the count, threshold-crossing probability for small lists
(the draws give it, but it is not reported yet).
