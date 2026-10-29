# Pre-registration: TV exit polls vs final results, and vs our simulation

Written and committed 29.10.2026 ~22:45 IST BEFORE any TV prediction was collected or any error computed.
(The commit hash of this file is the timestamp. Later edits must be separate commits with a stated reason.)

## Question
How far were the election-night (about 22:00) seat predictions published by Israeli TV channels from the final official seats, in K21-K25, and how does that compare with the error our simulation reports for a box-sample poll?

## Data rules
- Only public sources with a link (news sites, Wikipedia tables citing them). Each number is stored with its source URL and an "as stated" note.
- Use the first exit-poll seat prediction broadcast on election night per channel (about 22:00). Later updates (mixed with counted boxes) are excluded.
- Final results: official final seats per list from the Central Elections Committee (or the Knesset), not the interim count.
- Only lists that either won seats or were predicted at least 1 seat by that channel enter the metric. A list a channel did not give seats counts as predicted 0 seats.
- If a channel published ranges (e.g. 6-7), use the midpoint and flag it; if only the broadcast headline numbers exist, use those. No imputing from memory: anything not found in a source is left empty, and the channel-election cell is excluded.

## Metrics (fixed now)
1. PRIMARY: seats out of place = (sum over lists of |predicted - final seats|) / 2. Same definition as `seats_misallocated` in `model/exitpoll.py` and `model/backtest.py`.
2. SECONDARY: mean absolute seat error per list over the lists in the set above.
3. SECONDARY: error in the seats of the largest final list, and error in the gap between the two largest final lists.
No bloc metric: bloc membership is arguable and was not defined in advance, so we do not report one.

## Aggregation
Per channel-election cell, then the mean and the range over cells. Report n (cells). No significance test: with 5 elections and 3-4 channels the sample is small; we report the numbers and the ranges, not a "winner".

## Comparison with our simulation (kept separate)
Our number is the simulated `seats_misallocated`, mean absolute seat error per list, and top-list errors, computed with the SAME definitions for the design `strat_prior` at 60 boxes x 100 interviews on K22-25 and for the same design under the "hard_both" assumptions. These are development data (the designs were chosen after seeing them). The TV numbers are real broadcasts; ours is a simulation without field problems. A smaller simulated error therefore does NOT mean we would beat TV. K21 is not in our simulation (needs K20 profile; included only if the pipeline runs on it without changes). K26 TV predictions are recorded, but K26 is scored only when final official seats exist.

## What would count as evidence for "we beat TV"
Nothing in this comparison can. It is a baseline for the size of the TV error. Evidence would need a field poll with a list fixed before the election and this same metric.
