# Backtest results (v1)

Run: `python3 scripts/fetch_history.py && python3 -m model.backtest && python3 -m model.coverage && python3 -m model.plots`

IMPORTANT LIMITS
- Real arrival orders of past elections are not public. Orders are SIMULATED: random, small places first,
  large first, low turnout first, low Likud share first, high Likud share first. The politically biased orders are
  deliberately hard. Real orders are probably somewhere between random and biased.
- Truth for Knesset 22-25 is the official final station file. Truth for 2026 is the current CEC file
  without envelopes (regular boxes only; envelopes are not final).
- "Counted %" is the share of voting places, not of votes.
- Seat metric: half the sum of absolute seat differences over lists (seats that ended up on the wrong list).
- The 2026 surplus agreements are taken from public reporting; verify the letters before using 2026 seat numbers.

Figure: `docs/backtest_seats.png`. Pooled over Knesset 22-26 replays (numbers from results/backtest.csv):

| places counted | random order: counted-so-far | random order: projection | worst biased order: counted-so-far | worst biased order: projection |
|---|---|---|---|---|
| 1% | 13.0 | 4.5 | 100.0 | 69.4 |
| 5% | 5.5 | 2.3 | 98.6 | 60.8 |
| 20% | 2.6 | 2.2 | 75.4 | 20.4 |
| 40% | 1.9 | 1.4 | 35.6 | 5.8 |
| 80% | 0.3 | 0.5 | 17.8 | 3.4 |

Reading: the projection removes most of the bias that politically ordered counting creates, and helps
a lot at small counted shares. It is not a polished model: at 1% the error under random order is still
about 4-5 seats misallocated, and under biased orders it is large. 20 to 40% counted is where it becomes reliable.

Interval check (`model/coverage.py`, random order, nominal 80% interval for each list's seats, lists with seats only):
actual coverage 85% at 2-20% counted and 93% at 40%. Under biased orders the intervals are too narrow (not measured yet).

Compared with the claim of Votes26 (54/49/17 vs about 53/48/19 after 1.7% counted, bloc seats, unverified):
not comparable yet, our metric is per list and the orders differ. A fair comparison needs the real 2026
arrival order, which we only started recording at 13:09 IST on 29.10 (after the regular boxes were already in the file).

## Envelopes (v1, `model/envelopes.py`)
Test: predict Knesset 25 envelope list shares from K25 regular-box shares plus the mean (envelope minus regular)
difference of K22-24, same list letters. Mean absolute error over all lists: 0.565 share points for the naive
"same as regular boxes", 0.531 with the historical lean. A small gain. It fixes the Haredi/Arab dip (e.g. Shas 8.4% regular,
6.8% in envelopes, estimate 6.8%) but misses new swings (Religious Zionism 15.5% true vs 11.2% estimated). Envelope
votes were 10.7% of regular valid votes in K25. Output: `results/envelope_backtest.txt`. Envelope totals are not yet
wired into the seat projection.
