# open-count-model

Open-source model that predicts final Knesset seat counts from the order in which polling
stations (קלפיות) are published during the official count, plus the collector that records that
order. Code: MIT. Data: official Central Elections Committee (CEC) files, attributed below.

Status: early. Collector works; model is being built. See `docs/` for the plan and research notes.

## Why

During the count the CEC publishes a station-level file. Stations are not counted in random
order, so raw partial totals are biased. A model that compares each counted station with its own
past results and projects the swing to uncounted stations can give an early, honest estimate with
ranges. The missing public piece is the arrival order of stations. This repo records it.

## Layout

- `collector/` - records every version of the CEC live files with UTC timestamps.
- `data-raw/live/` - raw CEC snapshots from the 2026 count (`expb` by station, `expc` by locality), gzip, never edited.
- `data-raw/cec_history/` - not committed; filled by `scripts/fetch_history.py` (Knesset 18-25 by station).
- `scripts/` - data download and processing.
- `model/` - loaders, swing model, seat simulation, backtests.
- `docs/` - plan and research notes.

## Data sources and attribution

- Live 2026 count: CEC, https://votes26.bechirot.gov.il (files `media26.bechirot.gov.il/files/expb.csv`, `expc.csv`).
- Historical station results: CEC via https://data.gov.il/dataset/votes-knesset (portal terms: https://data.gov.il/terms).
- This is an independent project, not affiliated with the CEC.

## Collector

The CEC file host answers plain scripts with a bot challenge. We do not work around it. A normal
browser session loads the public page and reads the same public file, so `collector/watch.js` runs
inside a browser tab on `https://media26.bechirot.gov.il/`. Once a minute it sends a cheap HEAD request, and
when `Last-Modified`/ETag change it downloads the file and queues a gzip copy. `collector/harvest.js`
drains the queue and `collector/ingest_browser_result.py` writes
`data-raw/live/<UTC>/expb.csv.gz`, `expc.csv.gz`, `meta.json` and appends `polls.jsonl`.
Arrival order is then derived by diffing consecutive snapshots (`model/first_seen.py`).

Limits: a station's first-seen time is the first snapshot that contains it, so resolution is the CEC
publication interval, not per station. The file also carries "external envelope" rows (code 9999).
