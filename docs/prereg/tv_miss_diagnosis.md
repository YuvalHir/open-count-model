# Pre-registration: diagnosing TV exit-poll misses and re-testing the sampling design (diagnosis-v1)
Written before any of the numbers below were computed. Data: data/tv_exit_polls (TV first lists), results/exitpoll.csv (existing simulation, frozen designs/scenarios at tag exitpoll-designs-v1).

## Questions
Q1. Which lists/groups did the TV exit polls miss, in which direction (K21-K25, plus K26 provisional)?
Q2. Which assumed mechanism in our simulation reproduces that pattern: (a) no problem, (b) shy Likud voters (shy15), (c) Likud voters answer less (refuse20), (d) Haredi/Arab voters answer less (hard_nr), (e) Haredi/Arab places refuse interviewers (place_refuse), (f) both (hard_both), (g) random wrong answers (noise10).
Q3. Boxes vs interviews per box at a fixed interview budget, with the design effect.
Q4. Does combining the exit sample with the live CEC count help (tested later, separate pre-registration).

## Definitions (fixed now)
- Groups: Likud; Haredi = Shas + UTJ; Arab = Joint List + Ra'am + Hadash-Ta'al (+Balad where separate); Rest = all other lists.
- Signed group error for a TV poll = (sum of predicted seats in group) - (sum of final seats in group). Final = CEC official (K21-25).
- Simulation signed group error = mean over repetitions of (group seats from the sample estimate) - (group seats from the true box results), K22-25, design pps_ratio (plain size-weighted draw) and strat_prior, 60 places x 100 interviews, 100 repetitions.
- Mechanism fit = (i) number of (election x group) cells, out of 16 (K22-25 x 4 groups), where the sign of the mean TV signed error (mean over channels) equals the sign of the simulated one (cells where either |value| < 0.5 seats count as no-sign and are excluded); (ii) mean absolute difference in seats between TV and simulated group errors. No threshold for "reproduces": we report both numbers, and that a match is consistency, not proof.
- Published explanations by pollsters/journalists are reported separately with links, labelled "what they said".
- Q3: grid n in {30,60,120} x m in {50,100,200,400 where available}; metric: seats out of place (same as the primary metric) and mean share error, at equal budgets n*m. Design effect = Var(estimate error of top list) / (p(1-p)/(n*m)).
- K26 is not an independent holdout. K22-25 are development data for our own methods; this analysis is descriptive/diagnostic.
- No claim of beating TV unless a real held-out test (not simulation) shows it.
