"""Signed group errors of TV exit polls (pre-registered in docs/prereg/tv_miss_diagnosis.md)."""
import csv, collections, os
D = os.path.join(os.path.dirname(__file__), "..", "data", "tv_exit_polls")
def grp(l):
    if l == "Likud": return "Likud"
    if l in ("Shas", "UTJ"): return "Haredi"
    if l in ("Joint List", "Ra'am", "Hadash-Ta'al", "Ra'am-Balad"): return "Arab"
    return "Rest"
def load(f): return list(csv.DictReader(open(os.path.join(D, f), encoding="utf-8")))
def run():
    fin = collections.defaultdict(lambda: collections.defaultdict(int))
    for r in load("official_final_seats.csv"): fin[r["election"]][grp(r["list"])] += int(r["seats"])
    P = collections.defaultdict(lambda: collections.defaultdict(int))
    meta = {}
    for r in load("tv_exit_polls.csv"):
        if r["complete"] != "full" or r["source_tier"] not in ("A", "B") or r["election"] not in fin: continue
        P[(r["election"], r["channel"])][grp(r["list"])] += int(r["seats"])
    rows = []
    for (e, ch), g in sorted(P.items()):
        for k in ("Likud", "Haredi", "Arab", "Rest"):
            rows.append(dict(election=e, channel=ch, group=k, pred=g[k], final=fin[e][k], signed_err=g[k] - fin[e][k]))
    out = os.path.join(os.path.dirname(__file__), "..", "results", "tv_group_errors.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
    agg = collections.defaultdict(list)
    for r in rows: agg[(r["election"], r["group"])].append(r["signed_err"])
    print("election group mean_signed_err (seats, predicted - final), n_channels")
    for (e, k), v in sorted(agg.items()): print(e, k, round(sum(v) / len(v), 2), len(v), v)
    for k in ("Likud", "Haredi", "Arab", "Rest"):
        v = [r["signed_err"] for r in rows if r["group"] == k]; print("ALL", k, round(sum(v) / len(v), 2), len(v))
if __name__ == "__main__": run()
