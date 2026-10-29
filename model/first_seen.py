"""Derive per-box "first seen" times by diffing consecutive live snapshots of expb.csv.

Box identity = (loc_code, station). A box is "new" in snapshot i if it is absent from i-1.
Output: DataFrame with loc_code, station, first_seen_utc, snapshot (stamp), valid.
Resolution is the interval between snapshots the CEC actually published, not per box.
Rows already present in the first snapshot get first_seen = that snapshot's time and
are flagged `in_first_snapshot` (their true arrival time is unknown).
"""
import json, os
import pandas as pd
from .load import live_snapshots, load_live

def first_seen() -> pd.DataFrame:
    seen, rows = set(), []
    for i, (stamp, d) in enumerate(live_snapshots()):
        meta = json.load(open(os.path.join(d, "meta.json")))
        lm = (meta.get("expb") or {}).get("last_modified")
        df = load_live(d)
        keys = list(zip(df.loc_code, df.station))
        for (lc, st), v, env in zip(keys, df.valid, df.is_envelope):
            if (lc, st) not in seen:
                seen.add((lc, st))
                rows.append(dict(loc_code=lc, station=st, snapshot=stamp, cec_last_modified=lm,
                                 valid=v, is_envelope=env, in_first_snapshot=(i == 0)))
    return pd.DataFrame(rows)

if __name__ == "__main__":
    f = first_seen()
    print(len(f), "boxes;", int(f.in_first_snapshot.sum()), "already present in first snapshot")
    print(f.groupby("snapshot").size())
