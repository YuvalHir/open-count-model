# How the model works (plain language)

## The problem
While votes are counted, the Central Elections Committee (CEC) publishes results station by station.
Stations do not arrive in random order: small and rural stations, Arab and Haredi towns, kibbutzim and
the "double envelope" votes each come at different times. If you just add up what has arrived, the
total is biased toward whoever voted in the early stations. The model tries to answer: "given what has
arrived and WHERE it came from, what will the final result be?"

## Steps
1. **Record.** The collector saves every version of the official CEC file with a timestamp. Comparing
   consecutive versions shows which stations are new (the arrival order).
2. **Compare each station with itself.** For every polling place that already reported, we look up the
   same place in the previous election (matched by locality and box number) and see how it changed.
3. **Learn the swing.** A regression (ridge) learns, from the places counted so far, how each party's
   share now depends on the previous election's shares in the same place, turnout and size. So it learns,
   for example, where former Yesh Atid voters went, without anyone writing a party-to-party mapping.
4. **Fill in the places not yet counted.** For every place not yet counted, the model takes its previous
   result, applies the learned swing, and scales its size by how turnout has changed in counted places.
   Late places are predicted from their own history, not from the early ones.
5. **Add up.** Counted votes plus predicted votes give a national total per list.
6. **Seats.** Lists under the 3.25% threshold are dropped, seats go by Bader-Ofer with the surplus-vote
   agreements. The code reproduces the official Knesset 25 allocation exactly (tests/test_seats.py).
7. **Ranges (Monte Carlo).** `project_draws` repeats steps 3-5 200 times. Each repeat refits on a random
   resample of the counted localities and adds random local noise taken from the model's own past errors.
   Every repeat gives its own seat table, so we get a seat range and the probability a list passes the
   threshold. `python -m model.simulate` prints it.

## Does it guess which stations arrived?
No guess is needed for counted stations: the file says what has arrived. For uncounted stations the
model assumes they exist and behave like their own past, not like the stations that arrived first. The
arrival order itself is NOT predicted. It matters because a biased order makes the learned swing less
representative (see the backtest with "worst biased orders", docs/backtest.md). Real orders are only
available from now on (collector), so we can later test whether order carries information.
Not built yet: in the live run the list of still-uncounted places has to come from the previous
election's list of places; that wiring is the next step.

## Measured speed
On 2 CPU cores, Knesset 25 replayed with 5% of 6,306 places counted: 200 Monte Carlo draws take about
2.2 seconds, seat allocation for all draws 0.006 s. 1,000 draws is about 11 s. A full backtest of all
elections and orders is a few minutes.

## Sector distortions
- **Handled implicitly:** because the swing is fitted on each place's own previous result, Arab, Haredi,
  kibbutz and settlement places are predicted from their own past (an Arab town is predicted from its
  last Ra'am/Hadash/Ta'al shares). There is no separate sector label.
- **Not handled yet:** explicit sector effects, correlation between neighbouring towns, and the
  envelopes (about 6-10% of the vote, a different lean: Religious Zionism 15.5% vs 10.3% in K25). An
  envelope estimator exists (model/envelopes.py, small gain) but is not in the seat projection.
- **Place matching:** only 62-97% of the votes can be matched to the previous election because box
  numbers change; the rest use the locality or national profile. This is the biggest known weakness.

## Known limits
Ranges are checked only for random order (80% range covers the truth about 85% of the time). For biased
orders they are probably too narrow. Early in the count (about 1%) the result is still poor. No claim of
parity with any other model.
