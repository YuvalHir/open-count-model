# Open model: predicting final seats from the order polling stations are counted
Research notes, 29.10.2026. Labels: [OFFICIAL] [THIRD-PARTY] [CLAIM] [OPINION] [UNVERIFIED]. Written before the collector existed; see README for current status.

## 1. Feasible? What accuracy?
- Method as Votes26 describes it [CLAIM]: each counted station is compared to its own result in the previous election, then projected to uncounted stations, with a range. "Counted stations are not counted in random order" is stated on the site.
- Code and data are closed. The site publishes no error table that could be read. The 54/49/17 vs ~53/48/19 figure after 1.7% counted is a claim reported secondhand (a tweet), not verified here.
- Same idea is standard: US election-night "needle" models (NYT, Washington Post) project from already-counted precincts vs their previous results [MEDIA: https://www.washingtonpost.com/politics/2022/05/17/post-election-night-model/ , https://www.nytimes.com/article/election-2024-results-needle.html].
- [OPINION] Feasible. The hard part is not the maths but data: previous-election results per station (available) and the arrival order of stations in the live count (we must record it). Expect results similar to his if the data is as good; no way to promise "better" before a backtest. Blocs are easier than single small parties near 3.25%. Arab-sector parties are the weakest spot (turnout swings, late/early counting by locality).
- Hard limit: double envelopes (soldiers, hospitals, prisoners, diplomats; hundreds of thousands of votes) are not in the regular station counts. They need a separate model (their vote share differs from the station average). Votes26 says they "can shift a seat".

## 2. Data needed and where to get it
| Piece | Source | Status |
|---|---|---|
| Final results per station, Knesset 25 (2022) | CEC data on data.gov.il, plus mirrors: https://www.over.org.il/archive/76df52af-930f-4ab6-bbe7-0609feb3dd3b (archive of the data.gov.il feed), https://votes25.bechirot.gov.il | OFFICIAL source, I did not download or open the file itself. License terms on data.gov.il: check per dataset. |
| Knesset 22 (2019 Sep) per station | https://www.odata.org.il/dataset/https-quantitatively-club (CSV, listed as CC-BY, last updated 2019, one row per ballot location with lat/lon) ; https://www.over.org.il/versions/987a6bac-303a-4b6a-9a4a-bf5a838f0730 | THIRD-PARTY mirror of CEC data |
| Knesset 19-24 per station | Not confirmed. Leads: https://github.com/shaielc/Behirot (has 2022 and 2026 folders), https://github.com/harelc/elections-vote-transfer, https://github.com/JacobWeinbren/Israel-Revised. CEC old sites (votesNN.bechirot.gov.il) likely hold station files; the Wayback Machine is the fallback | UNVERIFIED, must open each |
| Locality-level results all elections, open JSON/CSV | https://bechirot.fyi , https://israelvoting.com/data (static JSON, "no key, no limit") | THIRD-PARTY, locality level only |
| Live 2026 count per station | CEC site https://votes26.bechirot.gov.il . A third-party site archives a polling-station CSV during the count: https://github.com/EladHeller/israel-elections (commit of 29.10 "Archive polling-station CSV alongside locality results"). netunim.co.il also publishes partial results by locality and station with snapshot times: https://www.netunim.co.il/yishuv/bchirot | Exists. Whether Elad's archive includes timestamps per snapshot: UNVERIFIED. Repo license: I could not find a LICENSE file, so ask him before reusing code. |
| Turnout per station by hour (09/12/16/20) | CEC, https://www.gov.il/he/pages/turnout_at_polling_stations (per ordinary station: registered, voted so far, turnout %, report hour; excludes external envelopes) [OFFICIAL] | Great covariate: tells how much this election differs from 2022 per station before any count |
| Station metadata (locality, address, sector, lat/lon) | Fields exist in the CEC files (city code, station number, ballot location); odata.org.il file above has lat/lon | Partly verified |
| Over-time snapshots of the CEC feed | over.org.il keeps a first_seen timestamp per row for feeds it scrapes (archive page above) | Possible source of arrival times for some data; UNVERIFIED for 2026 stations |

### The key gap: arrival order
- What we need: for each station, the time it first appeared in the CEC feed (and the CEC's own "counted" timestamp if present).
- From now on: poll the CEC station file every 1-2 minutes on election night, store every raw file with a UTC timestamp, then diff to get first-seen time per station. Keep raw files, not just parsed ones. Run from a normal server (we already learned the CEC site blocks plain scripts, so we may need a browser or proper headers; check terms of use before heavy polling) [OPINION].
- This count: no station-level snapshots existed before the collector in this repo started on 2026-10-29 13:09 IST (11:09 UTC). Earlier arrival order can only be partly rebuilt from third-party archives, at snapshot resolution.
- Past elections: arrival order is almost certainly not published retroactively; backtesting on 2022 would need an archived live feed (Wayback captures of votes25 are a long shot). Alternative backtest: simulate plausible orders (see section 4).

## 3. Method design
1. Unit = station (ballot box). Features: previous result per list (2022, and earlier), registered voters, locality, sector (Arab, Haredi, secular, kibbutz, settlement...), turnout so far today, region, station size.
2. Swing: for each list, change in vote share vs 2022 in each counted station. Because parties merged and split (Yesh Atid, National Unity, Religious Zionism, Labor/Meretz...), map 2022 lists to 2026 lists with a transfer matrix (harelc/elections-vote-transfer is a starting point). Simplest: model blocs and a few big lists.
3. Projection: regress counted-station swing on station features, predict swing for uncounted stations, rebuild totals. Start with ridge regression / gradient boosting; upgrade to hierarchical Bayesian (locality and sector partial pooling), as in the Washington Post model. Same shape as the "needle" approach.
4. Arrival order matters because early stations are unrepresentative (small, rural, early-reporting localities). The model must condition on features, not assume random order. A "counted stations are representative" assumption is the failure mode.
5. Uncertainty: posterior or bootstrap/conformal intervals on each list's vote share; propagate by simulation (e.g. 5,000 draws) through threshold and Bader-Ofer with surplus agreements; report seat ranges and probability of 61+. Probability a list passes 3.25%.
6. Double envelopes: separate component; use past elections' envelope share and lean (2022 external envelope data in final results) with a wide prior.
7. Boundary changes: stations are renumbered/merged. Match by (locality, station number) first; fall back to address/lat-lon and to locality-level results when no match. Report the share of votes matched.
8. Allocation: Bader-Ofer, 3.25% threshold, surplus agreements only when both sides pass (see also EladHeller's calc-elections.ts, license unchecked).

## 4. Backtest plan and what we can do now
- Now: (a) download the 2022 and 2019 station files, build the station keys and the 2022-to-2026 matching; (b) once the final 2026 station file is published, compute per-station swings; (c) simulate arrival orders (random, by size, by locality type, by an order learned from this count if recovered) and see how fast error falls as counted % grows; report error at 1%, 5%, 20%, 50%.
- Fair test of the sort Votes26 claims: replay this election's recorded order, at each snapshot predict final seats, compare to the final count. Needs the order, see section 2.
- Backtest older elections only if order data exists; otherwise use simulated orders and say so.
- Metrics: seat error per list, bloc error, threshold calls, interval coverage (do 80% ranges contain truth 80% of the time).

## 5. Repo and simplest plan
- License: code MIT or Apache-2.0; derived data CC-BY or ODbL, keeping CEC attribution. Check the CEC terms of reuse (not verified here).
- Structure: /data-raw (hash-checked downloads, never edited), /data-processed, /collector (live poller storing timestamped raw files), /model (swing, projection, uncertainty), /allocation (Bader-Ofer), /backtest, /docs (method, data sources, limitations), /site.
- Simplest version: Phase 0, collector running and tested on a past/dummy feed. Phase 1, 2022 station file loaded, bloc-level swing model using only (locality, sector, size) features. Phase 2, seat simulation with ranges. Phase 3, double envelopes and hourly turnout. Phase 4, hierarchical model and a public backtest report. Before the next election, run the collector for every by-election or local-style test day if possible.

## Source ledger
Official: https://www.gov.il/he/pages/turnout_at_polling_stations ; https://votes26.bechirot.gov.il ; https://votes25.bechirot.gov.il/ballotresults
Third-party data: https://www.over.org.il/archive/76df52af-930f-4ab6-bbe7-0609feb3dd3b ; https://www.odata.org.il/dataset/https-quantitatively-club ; https://bechirot.fyi/en/elections/25 ; https://israelvoting.com/data ; https://www.netunim.co.il/yishuv/bchirot ; https://github.com/EladHeller/israel-elections ; https://github.com/shaielc/Behirot ; https://github.com/harelc/elections-vote-transfer
His claim: https://votes26.com/about ; https://x.com/Nehemia_GA/status/2115742777669513324 (not opened by me)
Other open project: https://elections.gtmascode.dev (polls and candidates database; no station-level count data seen)
Method background: https://www.washingtonpost.com/politics/2022/05/17/post-election-night-model/ ; https://www.nytimes.com/article/election-2024-results-needle.html
Not verified: contents/format of any station CSV, license terms of data.gov.il files, Votes26 error numbers, our own station-level logs.
