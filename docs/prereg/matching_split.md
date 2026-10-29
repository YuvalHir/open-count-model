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

## Addendum A (written after the `split` run, before any run of the strategies below)
Result of `split` (reported separately): K25->K26 match 75.75% -> 76.07%, no projection gain. Diagnosis: K26 and K25 have almost the same number of boxes (12,005 vs 11,707; Tel Aviv 766 vs 736) but K26 uses many more distinct integer place numbers (8,679 vs 6,306 places; Tel Aviv 424 vs 304), so K25 places are all consumed by the 1:1 `fill` and the remaining K26 places have no K25 partner left. Reuse of a K25 place by several K26 places is needed from the start.
New strategies (same decision rule, same development and target pairs):
- `cum` : per locality, order places by number. Anchors = same number and registered voters within a factor 1.28 (|log ratio| < 0.25). Between consecutive anchors (and before the first / after the last), place each K26 place at the midpoint of its cumulative registered voters and assign it to the K25 place whose cumulative interval (in the same segment) contains that midpoint. Segments whose total registered voters differ by more than a factor of 2 are skipped. Many K26 places can share one K25 place (votes split by registered voters, existing code).
- `fillcum` : `fill`, then `cum` only for the places `fill` left unmatched, using all K25 places of the locality.

## Results (29.10.2026, results/matching_split.csv and results/matching_cum.csv)
- `split`: match rate 92.03% -> 92.35% (K22-26 mean); K25->K26 75.75% -> 76.07%; no projection change. Not better.
- `cum`: match rate falls (84.5% mean); projection worse in most pairs. Worse.
- `fillcum`: match rate rises to 96.1% (mean), but projection is worse: K22-26 mean share error at 20% counted 0.18 -> 0.22 pp, seats 1.70 -> 1.85; on K26 share error 0.13 -> 0.34 pp. Decision rule: not better. Worse on the target pair.
- Reading: the extra matches are mostly wrong pairs. A wrong matched profile hurts more than falling back to the locality profile. The cumulative-size alignment assumes boxes keep their order inside a locality; K26 numbering does not support that. Negative result kept. `fill` stays the default.
- Unresolved: the 76% is a rate of K26 votes that have a plausible K25 partner by number and size. Better evidence for pairing (addresses of K25 and K26 together with a trust rule) was tried before (site) and gave no K26 gain.
