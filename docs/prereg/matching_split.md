# Pre-registration: split-aware place matching (matching-split-v1)
Written 29.10.2026 before the strategy was run.

## Diagnosis (descriptive, K25 -> K26, `fill` strategy, current file)
Only 76% of K26 votes sit in places matched to a K25 place (8,679 places, 2,441 unmatched). Unmatched votes are almost entirely in big cities (Tel Aviv, Jerusalem, Haifa, Rishon...), not in new localities (0.08% of votes). Example: Tel Aviv has 424 K26 places and 304 K25 places; many K25 places have 2,000 to 5,000 registered voters (several sub-boxes merged by our "integer part" rule) while the K26 places with the same numbers have about 600. A one-to-one size match cannot link a 2,700-voter K25 place to four 600-voter K26 places.

## Strategy "split" (new, `model/matching.py`)
Start from `fill`. Then, inside each locality, for the leftover K26 places and the leftover K25 places: treat a K25 place of registered size R as k = max(1, round(R / s)) equal parts of size R/k, where s is the median registered size of the locality's leftover K26 places; assign each leftover K26 place to a part by minimum |log(size ratio)| plus the same small number-proximity penalty as `fill`, with cap 0.5 on the log size mismatch. A K25 place can serve at most k K26 places (its votes are split by registered voters, existing code).
Nothing else changes. Frozen strategies (exact, fill, site, site2) are untouched (tag matching-rules-v1).

## Test (tag before running)
Metrics: share of votes matched; projection error (share MAE in points and seats out of place) with the same harness as `model/match_eval.py` (ridge, 5% and 20% counted, random order, 4 seeds, and the low-Likud-first order), per election pair.
Development: pairs K21->22 ... K24->25 (K22-25 results). Target pair: K25->K26 on the live file (K26 is not final and not an independent holdout: reported but labelled).
Decision rule: "better" = projection error at least 5% lower than `fill` averaged over K22-25 pairs and not worse on K26; match rate alone is not enough (earlier lesson: higher match did not improve projection).
Negative results will be reported.
