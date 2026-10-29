"""TV exit-poll comparison, preregistered in docs/prereg/tv_exit_poll_comparison.md (commit a80b1a7).
Predictions: data/tv_exit_polls/tv_exit_polls.csv. Official finals: data/tv_exit_polls/official_final_seats.csv.
Primary metric: seats out of place = sum_over_lists |pred-final| / 2 (missing prediction = 0)."""
import csv, collections, os
D = os.path.join(os.path.dirname(__file__), "..", "data", "tv_exit_polls")
def load(f): return list(csv.DictReader(open(os.path.join(D, f), encoding="utf-8")))
def metrics(pred, final):
    lists = {l for l, v in final.items() if v > 0} | {l for l, v in pred.items() if v >= 1}
    d = {l: abs(pred.get(l, 0) - final.get(l, 0)) for l in lists}
    top = sorted(final, key=lambda l: -final[l])[:2]
    gap = abs((pred.get(top[0], 0) - pred.get(top[1], 0)) - (final[top[0]] - final[top[1]]))
    return dict(out_of_place=sum(d.values()) / 2, mae_list=sum(d.values()) / len(d),
                top_err=abs(pred.get(top[0], 0) - final[top[0]]), top2_gap_err=gap, n_lists=len(d))
def main():
    fin = collections.defaultdict(dict)
    for r in load("official_final_seats.csv"): fin[r["election"]][r["list"]] = int(r["seats"])
    P = collections.defaultdict(dict)
    for r in load("tv_exit_polls.csv"):
        P[(r["election"], r["channel"], r["source_tier"], r["complete"])][r["list"]] = int(r["seats"])
    rows = []
    for (e, ch, tier, comp), p in P.items():
        if e not in fin: continue  # K26 recorded, not scored
        if comp != "full":
            rows.append(dict(election=e, channel=ch, source_tier=tier, complete=comp, scored="no (partial list)")); continue
        m = metrics(p, fin[e]); sums = sum(p.values())
        rows.append(dict(election=e, channel=ch, source_tier=tier, complete=comp, scored="yes", pred_sum=sums, **m))
    rows.sort(key=lambda r: (r["election"], r["channel"], r["source_tier"]))
    keys = ["election","channel","source_tier","complete","scored","pred_sum","out_of_place","mae_list","top_err","top2_gap_err","n_lists"]
    out = os.path.join(os.path.dirname(__file__), "..", "results", "tv_exit_poll_comparison.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, keys); w.writeheader(); [w.writerow({k: r.get(k, "") for k in keys}) for r in rows]
    for r in rows: print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})
    sc = [r for r in rows if r["scored"] == "yes" and r["source_tier"] in ("A", "B")]
    print("cells", len(sc), "mean out_of_place", sum(r["out_of_place"] for r in sc) / len(sc),
          "range", min(r["out_of_place"] for r in sc), max(r["out_of_place"] for r in sc))
if __name__ == "__main__": main()
